"""
FFmpeg-based media processing functions.
Handles audio extraction and frame extraction from video files.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional

from .config import settings
from .logger import setup_logger

logger = setup_logger(__name__)


def check_ffmpeg_available() -> bool:
    """
    Check if FFmpeg is installed and available in PATH.
    
    Returns:
        True if FFmpeg is available, False otherwise
    """
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def extract_audio(
    video_path: str,
    output_path: str,
    sample_rate: int = 16000,
    channels: int = 1,
    codec: str = "pcm_s16le"
) -> str:
    """
    Extract audio from a video file to WAV format.
    
    Args:
        video_path: Path to input video file
        output_path: Path where audio will be saved
        sample_rate: Audio sample rate (Hz)
        channels: Number of audio channels (1 for mono, 2 for stereo)
        codec: Audio codec to use
    
    Returns:
        Path to extracted audio file
    
    Raises:
        FileNotFoundError: If video file doesn't exist or FFmpeg not available
        subprocess.CalledProcessError: If FFmpeg extraction fails
    """
    video_path = str(video_path)
    output_path = str(output_path)
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not check_ffmpeg_available():
        raise FileNotFoundError("FFmpeg not found. Please install FFmpeg to use this tool.")
    
    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    logger.info(f"Extracting audio from {video_path} to {output_path}")
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",  # Disable video
        "-acodec", codec,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-y",  # Overwrite output file
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"Audio extraction completed: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Audio extraction failed: {e.stderr}")
        raise


def extract_frames(
    video_path: str,
    output_dir: str,
    fps: float = 1.0,
    max_frames: Optional[int] = None
) -> list[str]:
    """
    Extract frames from a video file.
    
    Args:
        video_path: Path to input video file
        output_dir: Directory where frames will be saved
        fps: Frames per second to extract (default 1.0)
        max_frames: Maximum number of frames to extract (None for all)
    
    Returns:
        List of paths to extracted frame images
    
    Raises:
        FileNotFoundError: If video file doesn't exist or FFmpeg not available
        subprocess.CalledProcessError: If FFmpeg extraction fails
    """
    video_path = str(video_path)
    output_dir = str(output_dir)
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not check_ffmpeg_available():
        raise FileNotFoundError("FFmpeg not found. Please install FFmpeg to use this tool.")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info(f"Extracting frames from {video_path} at {fps} fps to {output_dir}")
    
    frame_pattern = os.path.join(output_dir, "frame_%04d.jpg")
    
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vf", f"fps={fps}",
        "-y",  # Overwrite output files
        frame_pattern
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Frame extraction failed: {e.stderr}")
        raise
    
    # Collect extracted frames
    frame_files = sorted(
        [f for f in os.listdir(output_dir) if f.startswith("frame_") and f.endswith(".jpg")]
    )
    frame_paths = [os.path.join(output_dir, f) for f in frame_files]
    
    # Limit frames if max_frames is set
    if max_frames and len(frame_paths) > max_frames:
        # Sample frames evenly across the video
        step = len(frame_paths) // max_frames
        frame_paths = frame_paths[::step][:max_frames]
        
        # Keep track of which frames we're keeping
        kept_frames = {os.path.basename(p) for p in frame_paths}
        
        # Delete unused frames to save space
        for frame_file in frame_files:
            if frame_file not in kept_frames:
                try:
                    os.remove(os.path.join(output_dir, frame_file))
                except OSError:
                    pass
    
    logger.info(f"Extracted {len(frame_paths)} frames")
    return frame_paths


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of a video file in seconds.
    
    Args:
        video_path: Path to video file
    
    Returns:
        Duration in seconds
    
    Raises:
        FileNotFoundError: If video file doesn't exist or FFmpeg not available
        ValueError: If duration cannot be determined
    """
    video_path = str(video_path)
    
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    if not check_ffmpeg_available():
        raise FileNotFoundError("FFmpeg not found. Please install FFmpeg to use this tool.")
    
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1:noprint_wrappers=1",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        duration = float(result.stdout.strip())
        return duration
    except (subprocess.CalledProcessError, ValueError) as e:
        logger.error(f"Could not determine video duration: {e}")
        raise ValueError(f"Could not determine duration of {video_path}") from e
