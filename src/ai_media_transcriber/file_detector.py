"""
File type detection utilities.
Determines whether input is video, image, or audio.
"""
import os
from pathlib import Path


# Supported file extensions by type
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m3u8',
    '.mts', '.ts', '.m2ts', '.mxf', '.ogv', '.3gp', '.3g2'
}

IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.tif',
    '.svg', '.ico', '.jfif', '.heic', '.heif'
}

AUDIO_EXTENSIONS = {
    '.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.wma', '.aiff',
    '.alac', '.opus', '.speex'
}


class FileType:
    """File type constants."""
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    UNKNOWN = "unknown"


def get_file_extension(file_path: str) -> str:
    """Get file extension in lowercase."""
    return Path(file_path).suffix.lower()


def detect_file_type(file_path: str) -> str:
    """
    Detect file type based on extension.
    
    Args:
        file_path: Path to file
    
    Returns:
        One of: 'video', 'image', 'audio', 'unknown'
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    file_path = str(file_path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    ext = get_file_extension(file_path)
    
    if ext in VIDEO_EXTENSIONS:
        return FileType.VIDEO
    elif ext in IMAGE_EXTENSIONS:
        return FileType.IMAGE
    elif ext in AUDIO_EXTENSIONS:
        return FileType.AUDIO
    else:
        return FileType.UNKNOWN


def is_batch_image_input(file_paths: list[str]) -> bool:
    """
    Check if input is a batch of images.
    
    Args:
        file_paths: List of file paths
    
    Returns:
        True if all are image files
    """
    if not file_paths:
        return False
    
    for path in file_paths:
        if detect_file_type(path) != FileType.IMAGE:
            return False
    
    return True


def validate_file_type(file_path: str, expected_type: str) -> bool:
    """
    Validate that a file is of expected type.
    
    Args:
        file_path: Path to file
        expected_type: Expected file type ('video', 'image', or 'audio')
    
    Returns:
        True if file matches expected type
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file type doesn't match expected_type
    """
    detected = detect_file_type(file_path)
    
    if detected != expected_type:
        raise ValueError(
            f"Expected {expected_type} file, but got {detected}: {file_path}"
        )
    
    return True
