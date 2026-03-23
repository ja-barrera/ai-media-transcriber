"""
OpenAI API client for AI Media Transcriber.
Handles Whisper transcription, vision analysis, and text summarization.
"""
import base64
from typing import Optional
from pathlib import Path

from openai import OpenAI
from openai.types.audio import Transcription

from .config import settings
from .logger import setup_logger
from .types import Transcript, FrameAnalysis

logger = setup_logger(__name__)


class OpenAIClient:
    """
    Wrapper around OpenAI API for video analysis tasks.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (uses env variable if not provided)
        
        Raises:
            ValueError: If API key is not provided or configured
        """
        api_key = api_key or settings.openai_api_key
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or AMT_OPENAI_API_KEY"
            )
        
        self.client = OpenAI(api_key=api_key)
        self.transcription_model = settings.openai_model_transcription
        self.vision_model = settings.openai_model_vision
        self.summarization_model = settings.openai_model_summarization
        logger.info("OpenAI client initialized")
    
    def transcribe_audio(self, audio_path: str) -> Transcript:
        """
        Transcribe audio using Whisper.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, etc.)
        
        Returns:
            Transcript object containing transcription and metadata
        
        Raises:
            FileNotFoundError: If audio file not found
            Exception: If transcription fails
        """
        audio_path = str(audio_path)
        
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Transcribing audio: {audio_path}")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                result = self.client.audio.transcriptions.create(
                    model=self.transcription_model,
                    file=audio_file,
                    response_format="json"
                )
            
            # Whisper result is a Transcription object
            transcript_text = result.text
            
            # Calculate word count
            word_count = len(transcript_text.split())
            
            logger.info(
                f"Transcription completed: {word_count} words"
            )
            
            return Transcript(
                text=transcript_text,
                duration_seconds=0.0,  # Would need to calculate from audio
                word_count=word_count
            )
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def analyze_frame(self, image_path: str) -> str:
        """
        Analyze a single frame/image using GPT-4V.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Description of the image content
        
        Raises:
            FileNotFoundError: If image file not found
            Exception: If vision analysis fails
        """
        image_path = str(image_path)
        
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Analyzing frame: {image_path}")
        
        try:
            # Encode image to base64
            with open(image_path, 'rb') as img_file:
                image_data = base64.standard_b64encode(img_file.read()).decode('utf-8')
            
            # Determine media type from file extension
            ext = Path(image_path).suffix.lower()
            media_type_map = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }
            media_type = media_type_map.get(ext, 'image/jpeg')
            
            # Call GPT-4V via chat completions
            response = self.client.chat.completions.create(
                model=self.vision_model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": (
                                    "Provide a concise, objective description of what you see in this image. "
                                    "Focus on: people, objects, text, scenes, and actions. "
                                    "Keep the description to 2-3 sentences."
                                )
                            }
                        ]
                    }
                ]
            )
            
            description = response.choices[0].message.content
            logger.info(f"Frame analysis completed")
            return description
        
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            raise
    
    def summarize(
        self,
        transcript: str,
        frame_descriptions: list[str] = None,
        max_tokens: Optional[int] = None
    ) -> dict:
        """
        Generate a summary from transcript and optional frame descriptions.
        
        Args:
            transcript: Full transcript text
            frame_descriptions: List of frame descriptions (optional)
            max_tokens: Maximum tokens for response (uses config default if not set)
        
        Returns:
            Dictionary with summary, key_points, topics, and action_items
        
        Raises:
            Exception: If summarization fails
        """
        max_tokens = max_tokens or settings.openai_max_tokens_summary
        
        # Build context for summarization
        context = f"Transcript:\n{transcript}"
        
        if frame_descriptions:
            frame_text = "\n".join(
                f"- {desc}" for desc in frame_descriptions
            )
            context += f"\n\nScenes from video:\n{frame_text}"
        
        logger.info("Summarizing transcript and visual content")
        
        try:
            response = self.client.chat.completions.create(
                model=self.summarization_model,
                max_tokens=max_tokens,
                temperature=settings.openai_temperature,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional video analyst. "
                            "Analyze the provided transcript and visual descriptions. "
                            "Generate a structured summary including: "
                            "1. A brief title/topic\n"
                            "2. Comprehensive summary (2-3 paragraphs)\n"
                            "3. Key points (bullet list)\n"
                            "4. Topics covered\n"
                            "5. Action items or conclusions\n"
                            "Be concise and focus on the most important information."
                        )
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ]
            )
            
            summary_text = response.choices[0].message.content
            
            # Parse the structured response
            result = self._parse_summary_response(summary_text)
            
            logger.info("Summarization completed")
            return result
        
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise
    
    def _parse_summary_response(self, response_text: str) -> dict:
        """
        Parse structured summary response from GPT-4.
        
        Args:
            response_text: Raw response from GPT-4
        
        Returns:
            Dictionary with parsed summary components
        """
        # This is a simple parser - GPT-4 should return well-structured text
        # In production, you might want more robust parsing
        
        lines = response_text.strip().split('\n')
        
        result = {
            'title': None,
            'summary': '',
            'key_points': [],
            'topics': [],
            'action_items': []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # Detect section headers
            if line.lower().startswith('title'):
                current_section = 'title'
                result['title'] = line.split(':', 1)[-1].strip() if ':' in line else ''
            elif any(x in line.lower() for x in ['summary', 'overview']):
                current_section = 'summary'
            elif 'key point' in line.lower():
                current_section = 'key_points'
            elif 'topic' in line.lower():
                current_section = 'topics'
            elif any(x in line.lower() for x in ['action item', 'conclusion']):
                current_section = 'action_items'
            elif line and line.startswith('-'):
                # Bullet point
                item = line.lstrip('- ').strip()
                if current_section == 'key_points':
                    result['key_points'].append(item)
                elif current_section == 'topics':
                    result['topics'].append(item)
                elif current_section == 'action_items':
                    result['action_items'].append(item)
            elif line and current_section == 'summary' and not line.startswith('#'):
                result['summary'] += line + ' '
        
        result['summary'] = result['summary'].strip()
        
        # Ensure we have at least a basic title
        if not result['title']:
            result['title'] = "Video Analysis Summary"
        
        return result
    
    def chunk_transcript(
        self,
        transcript: str,
        chunk_size: int = 2000
    ) -> list[str]:
        """
        Split a transcript into manageable chunks.
        
        Args:
            transcript: Full transcript text
            chunk_size: Approximate token size per chunk (words ~= tokens for English)
        
        Returns:
            List of transcript chunks
        """
        words = transcript.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += 1
            
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        # Add remaining words
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        logger.info(f"Split transcript into {len(chunks)} chunks")
        return chunks
