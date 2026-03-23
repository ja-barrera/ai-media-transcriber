"""
File and directory utilities for AI Media Transcriber.
Handles temporary directories, artifact management, and cleanup.
"""
import os
import shutil
from pathlib import Path
from typing import Optional

from .config import settings
from .logger import setup_logger

logger = setup_logger(__name__)


class ArtifactManager:
    """
    Manages temporary directories and intermediate files for video processing.
    """
    
    def __init__(self, video_path: str, keep_artifacts: bool = False):
        """
        Initialize artifact manager for a video.
        
        Args:
            video_path: Path to the input video file
            keep_artifacts: Whether to preserve intermediate files after processing
        """
        self.video_path = str(video_path)
        self.video_name = Path(video_path).stem
        self.keep_artifacts = keep_artifacts
        self.temp_dir = settings.get_temp_dir(self.video_name)
        self.created_paths = []
    
    def get_audio_path(self) -> str:
        """Get path where audio should be extracted."""
        return os.path.join(self.temp_dir, "audio.wav")
    
    def get_frames_dir(self) -> str:
        """Get directory where frames should be extracted."""
        return os.path.join(self.temp_dir, "frames")
    
    def get_transcript_path(self) -> str:
        """Get path where transcript should be saved."""
        return os.path.join(self.temp_dir, "transcript.txt")
    
    def get_frame_analyses_path(self) -> str:
        """Get path where frame analyses should be saved."""
        return os.path.join(self.temp_dir, "frame_analyses.json")
    
    def ensure_temp_dir(self) -> str:
        """
        Create temporary directory structure.
        
        Returns:
            Path to temporary directory
        """
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"Created temporary directory: {self.temp_dir}")
        return self.temp_dir
    
    def track_created_file(self, path: str) -> str:
        """
        Track a file that was created during processing.
        
        Args:
            path: Path to the file
        
        Returns:
            The path (for convenience)
        """
        path = str(path)
        if path not in self.created_paths:
            self.created_paths.append(path)
        return path
    
    def cleanup(self) -> bool:
        """
        Clean up temporary files and directories.
        
        Returns:
            True if cleanup was performed, False if artifacts were kept
        """
        if self.keep_artifacts:
            logger.info(f"Keeping artifacts in: {self.temp_dir}")
            return False
        
        try:
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            return True
        except OSError as e:
            logger.warning(f"Failed to clean up {self.temp_dir}: {e}")
            return False
    
    def get_artifact_paths(self) -> dict[str, str]:
        """
        Get all saved artifact files.
        
        Returns:
            Dictionary mapping artifact type to file path
        """
        artifacts = {}
        
        audio_path = self.get_audio_path()
        if os.path.exists(audio_path):
            artifacts["audio"] = audio_path
        
        transcript_path = self.get_transcript_path()
        if os.path.exists(transcript_path):
            artifacts["transcript"] = transcript_path
        
        frames_dir = self.get_frames_dir()
        if os.path.isdir(frames_dir):
            artifacts["frames_dir"] = frames_dir
        
        frame_analyses = self.get_frame_analyses_path()
        if os.path.exists(frame_analyses):
            artifacts["frame_analyses"] = frame_analyses
        
        return artifacts


def ensure_output_directory(output_dir: str) -> str:
    """
    Ensure output directory exists.
    
    Args:
        output_dir: Path to output directory
    
    Returns:
        Absolute path to output directory
    """
    output_dir = os.path.abspath(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    return output_dir


def validate_video_file(video_path: str) -> bool:
    """
    Validate that a file exists and appears to be a video.
    
    Args:
        video_path: Path to video file
    
    Returns:
        True if file exists and appears valid
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file doesn't appear to be a video
    """
    video_path = str(video_path)
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not os.path.isfile(video_path):
        raise ValueError(f"Path is not a file: {video_path}")
    
    # Check file extension
    valid_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m3u8'}
    _, ext = os.path.splitext(video_path)
    
    if ext.lower() not in valid_extensions:
        logger.warning(
            f"File extension {ext} may not be a valid video format. "
            f"Valid: {', '.join(valid_extensions)}"
        )
    
    return True


def save_json_output(data: dict, output_path: str) -> str:
    """
    Save data as JSON file.
    
    Args:
        data: Dictionary to save
        output_path: Path where JSON will be saved
    
    Returns:
        Path to saved file
    """
    import json
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Saved JSON output: {output_path}")
    return output_path


def save_markdown_output(content: str, output_path: str) -> str:
    """
    Save content as Markdown file.
    
    Args:
        content: Markdown content to save
        output_path: Path where file will be saved
    
    Returns:
        Path to saved file
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Saved Markdown output: {output_path}")
    return output_path


def save_text_output(content: str, output_path: str) -> str:
    """
    Save content as plain text file.
    
    Args:
        content: Text content to save
        output_path: Path where file will be saved
    
    Returns:
        Path to saved file
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Saved text output: {output_path}")
    return output_path
