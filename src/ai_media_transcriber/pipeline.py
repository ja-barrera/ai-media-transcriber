"""
Main pipeline orchestrator for video analysis.
Coordinates extraction, transcription, frame analysis, and summarization.
"""
import time
from pathlib import Path
from typing import Optional

from .config import settings
from .logger import setup_logger
from .types import Transcript, FrameAnalysis, Summary, ProcessingConfig, ProcessingResult
from .ffmpeg_processor import extract_audio, extract_frames, get_video_duration
from .file_utils import ArtifactManager, validate_video_file
from .openai_client import OpenAIClient

logger = setup_logger(__name__)


class VideoAnalysisPipeline:
    """
    Main orchestrator for video analysis pipeline.
    Coordinates all stages: extraction, transcription, analysis, and summarization.
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Initialize the pipeline.
        
        Args:
            openai_api_key: OpenAI API key (uses env if not provided)
        """
        self.client = OpenAIClient(api_key=openai_api_key)
    
    def process_video(
        self,
        video_path: str,
        config: ProcessingConfig = None,
        output_dir: str = "output"
    ) -> ProcessingResult:
        """
        Process a video through the complete analysis pipeline.
        
        Args:
            video_path: Path to input video file
            config: Processing configuration (uses defaults if None)
            output_dir: Directory where results will be saved
        
        Returns:
            ProcessingResult with all analysis data
        
        Raises:
            FileNotFoundError: If video file not found
            Exception: If any pipeline stage fails
        """
        start_time = time.time()
        
        # Validate inputs
        validate_video_file(video_path)
        if config is None:
            config = ProcessingConfig()
        
        logger.info(f"Starting video analysis pipeline for: {video_path}")
        
        # Initialize artifact manager
        artifact_manager = ArtifactManager(
            video_path,
            keep_artifacts=config.keep_artifacts
        )
        artifact_manager.ensure_temp_dir()
        
        try:
            # Stage 1: Audio extraction
            logger.info("=" * 50)
            logger.info("STAGE 1: Extracting audio...")
            logger.info("=" * 50)
            audio_path = self._extract_audio(video_path, artifact_manager)
            
            # Stage 2: Transcription
            logger.info("=" * 50)
            logger.info("STAGE 2: Transcribing audio...")
            logger.info("=" * 50)
            transcript = self._transcribe_audio(audio_path)
            
            # Stage 3: Frame extraction and analysis
            logger.info("=" * 50)
            logger.info("STAGE 3: Extracting and analyzing frames...")
            logger.info("=" * 50)
            frame_analyses = self._analyze_frames(
                video_path,
                artifact_manager,
                config
            )
            
            # Stage 4: Summarization
            logger.info("=" * 50)
            logger.info("STAGE 4: Generating summary...")
            logger.info("=" * 50)
            
            # Extract frame descriptions
            frame_descriptions = [f.description for f in frame_analyses]
            
            summary_dict = self.client.summarize(
                transcript=transcript.text,
                frame_descriptions=frame_descriptions if frame_descriptions else None
            )
            
            # Create Summary object
            summary = Summary(
                title=summary_dict.get('title'),
                summary=summary_dict.get('summary', ''),
                key_points=summary_dict.get('key_points', []),
                topics=summary_dict.get('topics', []),
                action_items=summary_dict.get('action_items', []),
                duration_seconds=transcript.duration_seconds,
                transcript_word_count=transcript.word_count,
                frames_analyzed=len(frame_analyses)
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            logger.info("=" * 50)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Total processing time: {processing_time:.2f} seconds")
            logger.info("=" * 50)
            
            # Create result object
            result = ProcessingResult(
                video_path=str(video_path),
                transcript=transcript,
                frame_analyses=frame_analyses,
                summary=summary,
                processing_time_seconds=processing_time,
                output_paths={}  # Will be filled by caller
            )
            
            return result
        
        finally:
            # Cleanup artifacts if needed
            artifact_manager.cleanup()
    
    def _extract_audio(self, video_path: str, artifact_manager: ArtifactManager) -> str:
        """Extract audio from video."""
        audio_path = artifact_manager.get_audio_path()
        
        try:
            extract_audio(
                video_path=video_path,
                output_path=audio_path,
                sample_rate=settings.ffmpeg_audio_sample_rate,
                channels=settings.ffmpeg_audio_channels,
                codec=settings.ffmpeg_audio_codec
            )
            artifact_manager.track_created_file(audio_path)
            logger.info(f"✓ Audio extracted: {audio_path}")
            return audio_path
        
        except Exception as e:
            logger.error(f"✗ Audio extraction failed: {e}")
            raise
    
    def _transcribe_audio(self, audio_path: str) -> Transcript:
        """Transcribe audio using Whisper."""
        try:
            # Get file size to estimate duration
            file_size = Path(audio_path).stat().st_size
            # Rough estimate: 16-bit PCM at 16kHz = 32000 bytes/sec
            estimated_duration = file_size / 32000
            
            transcript = self.client.transcribe_audio(audio_path)
            transcript.duration_seconds = estimated_duration
            
            logger.info(f"✓ Transcription completed: {transcript.word_count} words")
            return transcript
        
        except Exception as e:
            logger.error(f"✗ Transcription failed: {e}")
            raise
    
    def _analyze_frames(
        self,
        video_path: str,
        artifact_manager: ArtifactManager,
        config: ProcessingConfig
    ) -> list[FrameAnalysis]:
        """Extract frames and analyze them."""
        frames_dir = artifact_manager.get_frames_dir()
        
        try:
            # Extract frames
            logger.info(f"Extracting frames at {config.fps} fps...")
            frame_paths = extract_frames(
                video_path=video_path,
                output_dir=frames_dir,
                fps=config.fps,
                max_frames=config.max_frames
            )
            
            if not frame_paths:
                logger.warning("No frames extracted")
                return []
            
            logger.info(f"✓ Extracted {len(frame_paths)} frames")
            
            # Analyze frames
            logger.info("Analyzing frames with vision model...")
            frame_analyses = []
            
            for idx, frame_path in enumerate(frame_paths):
                try:
                    logger.info(f"  Analyzing frame {idx + 1}/{len(frame_paths)}...")
                    description = self.client.analyze_frame(frame_path)
                    
                    # Calculate timestamp (approximate)
                    # timestamp = (frame_number / fps)
                    timestamp = (idx / config.fps) if config.fps > 0 else 0
                    
                    analysis = FrameAnalysis(
                        frame_number=idx + 1,
                        timestamp_seconds=timestamp,
                        image_path=str(frame_path),
                        description=description
                    )
                    frame_analyses.append(analysis)
                
                except Exception as e:
                    logger.warning(f"  ✗ Failed to analyze frame {idx + 1}: {e}")
                    continue
            
            logger.info(f"✓ Analyzed {len(frame_analyses)} frames")
            return frame_analyses
        
        except Exception as e:
            logger.error(f"✗ Frame analysis failed: {e}")
            raise
