"""
Output formatters for video analysis results.
Supports JSON, Markdown, and plain text formats.
"""
import json
from datetime import datetime
from typing import Optional

from .types import VideoProcessingResult
from .logger import setup_logger

logger = setup_logger(__name__)


class OutputFormatter:
    """Formats analysis results for output."""
    
    @staticmethod
    def format_video_as_json(result: VideoProcessingResult) -> str:
        """
        Format video result as JSON.
        
        Args:
            result: VideoProcessingResult object
        
        Returns:
            JSON string representation
        """
        data = {
            "video_path": result.video_path,
            "processing_time_seconds": result.processing_time_seconds,
            "transcript": {
                "text": result.transcript.text,
                "duration_seconds": result.transcript.duration_seconds,
                "word_count": result.transcript.word_count
            },
            "frames_analyzed": len(result.frame_analyses),
            "summary": {
                "title": result.summary.title,
                "summary": result.summary.summary,
                "key_points": result.summary.key_points,
                "topics": result.summary.topics,
                "action_items": result.summary.action_items
            }
        }
        
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def format_video_as_markdown(result: VideoProcessingResult) -> str:
        """
        Format video result as Markdown.
        
        Args:
            result: VideoProcessingResult object
        
        Returns:
            Markdown string representation
        """
        lines = []
        
        # Header
        lines.append(f"# {result.summary.title}")
        lines.append("")
        
        # Metadata
        lines.append("## Metadata")
        lines.append(f"- **Video**: {result.video_path}")
        lines.append(f"- **Duration**: {result.summary.duration_seconds:.1f} seconds")
        lines.append(f"- **Transcript**: {result.summary.transcript_word_count} words")
        lines.append(f"- **Frames Analyzed**: {result.summary.frames_analyzed}")
        lines.append(f"- **Processing Time**: {result.processing_time_seconds:.1f} seconds")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append(result.summary.summary)
        lines.append("")
        
        # Key Points
        if result.summary.key_points:
            lines.append("## Key Points")
            for point in result.summary.key_points:
                lines.append(f"- {point}")
            lines.append("")
        
        # Topics
        if result.summary.topics:
            lines.append("## Topics Covered")
            for topic in result.summary.topics:
                lines.append(f"- {topic}")
            lines.append("")
        
        # Action Items
        if result.summary.action_items:
            lines.append("## Action Items")
            for item in result.summary.action_items:
                lines.append(f"- {item}")
            lines.append("")
        
        # Full Transcript
        lines.append("## Full Transcript")
        lines.append("")
        lines.append(result.transcript.text)
        lines.append("")
        
        # Frame Descriptions
        if result.frame_analyses:
            lines.append("## Visual Scene Descriptions")
            lines.append("")
            for frame in result.frame_analyses:
                lines.append(f"### Frame {frame.frame_number} (@ {frame.timestamp_seconds:.1f}s)")
                lines.append(frame.description)
                lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_video_as_text(result: VideoProcessingResult) -> str:
        """
        Format video result as plain text.
        
        Args:
            result: VideoProcessingResult object
        
        Returns:
            Plain text string representation
        """
        lines = []
        
        # Header
        lines.append("=" * 70)
        lines.append(result.summary.title.center(70))
        lines.append("=" * 70)
        lines.append("")
        
        # Metadata
        lines.append("METADATA")
        lines.append("-" * 70)
        lines.append(f"Video:              {result.video_path}")
        lines.append(f"Duration:           {result.summary.duration_seconds:.1f} seconds")
        lines.append(f"Transcript Length:  {result.summary.transcript_word_count} words")
        lines.append(f"Frames Analyzed:    {result.summary.frames_analyzed}")
        lines.append(f"Processing Time:    {result.processing_time_seconds:.1f} seconds")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(result.summary.summary)
        lines.append("")
        
        # Key Points
        if result.summary.key_points:
            lines.append("KEY POINTS")
            lines.append("-" * 70)
            for i, point in enumerate(result.summary.key_points, 1):
                lines.append(f"{i}. {point}")
            lines.append("")
        
        # Topics
        if result.summary.topics:
            lines.append("TOPICS COVERED")
            lines.append("-" * 70)
            for topic in result.summary.topics:
                lines.append(f"• {topic}")
            lines.append("")
        
        # Action Items
        if result.summary.action_items:
            lines.append("ACTION ITEMS")
            lines.append("-" * 70)
            for i, item in enumerate(result.summary.action_items, 1):
                lines.append(f"{i}. {item}")
            lines.append("")
        
        # Full Transcript
        lines.append("FULL TRANSCRIPT")
        lines.append("-" * 70)
        lines.append(result.transcript.text)
        lines.append("")
        
        # Frame Descriptions
        if result.frame_analyses:
            lines.append("VISUAL SCENE DESCRIPTIONS")
            lines.append("-" * 70)
            for frame in result.frame_analyses:
                lines.append(f"Frame {frame.frame_number} (@ {frame.timestamp_seconds:.1f}s):")
                lines.append(f"  {frame.description}")
                lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_image_as_json(result) -> str:
        """
        Format image analysis result as JSON.
        
        Args:
            result: ImageProcessingResult object
        
        Returns:
            JSON string
        """
        data = {
            "image_paths": result.image_paths,
            "image_count": len(result.image_paths),
            "analyses": [
                {
                    "image_path": analysis.image_path,
                    "description": analysis.description
                }
                for analysis in result.analyses
            ],
            "processing_time_seconds": result.processing_time_seconds
        }
        
        if result.consolidated_summary:
            data["consolidated_summary"] = {
                "summary": result.consolidated_summary.consolidated_summary,
                "common_themes": result.consolidated_summary.common_themes
            }
        
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def format_image_as_markdown(result) -> str:
        """
        Format image analysis result as Markdown.
        
        Args:
            result: ImageProcessingResult object
        
        Returns:
            Markdown string
        """
        lines = []
        
        # Header
        title = "Image Analysis" if len(result.image_paths) == 1 else f"Image Analysis ({len(result.image_paths)} images)"
        lines.append(f"# {title}")
        lines.append("")
        
        # Metadata
        lines.append("## Metadata")
        lines.append(f"- **Images analyzed**: {len(result.image_paths)}")
        lines.append(f"- **Processing time**: {result.processing_time_seconds:.1f} seconds")
        lines.append("")
        
        # Consolidated summary (if available)
        if result.consolidated_summary:
            lines.append("## Consolidated Summary")
            lines.append(result.consolidated_summary.consolidated_summary)
            lines.append("")
            
            if result.consolidated_summary.common_themes:
                lines.append("### Common Themes")
                for theme in result.consolidated_summary.common_themes:
                    lines.append(f"- {theme}")
                lines.append("")
        
        # Individual analyses
        lines.append("## Individual Image Analyses")
        lines.append("")
        
        for idx, analysis in enumerate(result.analyses, 1):
            lines.append(f"### Image {idx}")
            lines.append(f"**File**: {analysis.image_path}")
            lines.append("")
            lines.append(analysis.description)
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_audio_as_json(result) -> str:
        """
        Format audio analysis result as JSON.
        
        Args:
            result: AudioProcessingResult object
        
        Returns:
            JSON string
        """
        data = {
            "audio_path": result.audio_path,
            "transcript": {
                "text": result.transcript.text,
                "duration_seconds": result.transcript.duration_seconds,
                "word_count": result.transcript.word_count
            },
            "summary": {
                "title": result.summary.title,
                "summary": result.summary.summary,
                "key_points": result.summary.key_points,
                "topics": result.summary.topics
            },
            "processing_time_seconds": result.processing_time_seconds
        }
        
        return json.dumps(data, indent=2, default=str)
    
    @staticmethod
    def format_audio_as_markdown(result) -> str:
        """
        Format audio analysis result as Markdown.
        
        Args:
            result: AudioProcessingResult object
        
        Returns:
            Markdown string
        """
        lines = []
        
        # Header
        lines.append(f"# {result.summary.title}")
        lines.append("")
        
        # Metadata
        lines.append("## Metadata")
        lines.append(f"- **Audio file**: {result.audio_path}")
        lines.append(f"- **Duration**: {result.transcript.duration_seconds:.1f} seconds")
        lines.append(f"- **Transcript length**: {result.transcript.word_count} words")
        lines.append(f"- **Processing time**: {result.processing_time_seconds:.1f} seconds")
        lines.append("")
        
        # Summary
        lines.append("## Summary")
        lines.append(result.summary.summary)
        lines.append("")
        
        # Key Points
        if result.summary.key_points:
            lines.append("## Key Points")
            for point in result.summary.key_points:
                lines.append(f"- {point}")
            lines.append("")
        
        # Topics
        if result.summary.topics:
            lines.append("## Topics Covered")
            for topic in result.summary.topics:
                lines.append(f"- {topic}")
            lines.append("")
        
        # Full Transcript
        lines.append("## Full Transcript")
        lines.append("")
        lines.append(result.transcript.text)
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_audio_as_text(result) -> str:
        """
        Format audio analysis as plain text.
        
        Args:
            result: AudioProcessingResult object
        
        Returns:
            Plain text string
        """
        lines = []
        
        # Header
        lines.append("=" * 70)
        lines.append(result.summary.title.center(70))
        lines.append("=" * 70)
        lines.append("")
        
        # Metadata
        lines.append("METADATA")
        lines.append("-" * 70)
        lines.append(f"Audio file:         {result.audio_path}")
        lines.append(f"Duration:           {result.transcript.duration_seconds:.1f} seconds")
        lines.append(f"Transcript length:  {result.transcript.word_count} words")
        lines.append(f"Processing time:    {result.processing_time_seconds:.1f} seconds")
        lines.append("")
        
        # Summary
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(result.summary.summary)
        lines.append("")
        
        # Key Points
        if result.summary.key_points:
            lines.append("KEY POINTS")
            lines.append("-" * 70)
            for i, point in enumerate(result.summary.key_points, 1):
                lines.append(f"{i}. {point}")
            lines.append("")
        
        # Topics
        if result.summary.topics:
            lines.append("TOPICS COVERED")
            lines.append("-" * 70)
            for topic in result.summary.topics:
                lines.append(f"• {topic}")
            lines.append("")
        
        # Full Transcript
        lines.append("FULL TRANSCRIPT")
        lines.append("-" * 70)
        lines.append(result.transcript.text)
        lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def format_and_save(
        result: VideoProcessingResult,
        output_dir: str,
        formats: list[str] = None
    ) -> dict[str, str]:
        """
        Format results and save to files.
        
        Args:
            result: VideoProcessingResult object
            output_dir: Directory where files will be saved
            formats: List of formats to save (json, markdown, text)
                    Defaults to ['json']
        
        Returns:
            Dictionary mapping format to output file path
        """
        import os
        from pathlib import Path
        
        if formats is None:
            formats = ['json']
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Base filename (without extension)
        video_name = Path(result.video_path).stem
        base_path = os.path.join(output_dir, f"{video_name}_analysis")
        
        output_paths = {}
        
        # JSON format
        if 'json' in formats:
            json_path = f"{base_path}.json"
            json_content = OutputFormatter.format_video_as_json(result)
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(json_content)
            output_paths['json'] = json_path
            logger.info(f"Saved JSON output: {json_path}")
        
        # Markdown format
        if 'markdown' in formats:
            md_path = f"{base_path}.md"
            md_content = OutputFormatter.format_video_as_markdown(result)
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            output_paths['markdown'] = md_path
            logger.info(f"Saved Markdown output: {md_path}")
        
        # Text format
        if 'text' in formats:
            txt_path = f"{base_path}.txt"
            txt_content = OutputFormatter.format_video_as_text(result)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            output_paths['text'] = txt_path
            logger.info(f"Saved text output: {txt_path}")
        
        return output_paths
