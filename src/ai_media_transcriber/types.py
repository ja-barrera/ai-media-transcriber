"""
Pydantic models for AI Media Transcriber data structures.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Transcript(BaseModel):
    """Represents a video transcript with metadata."""
    text: str = Field(..., description="Full transcription text")
    duration_seconds: float = Field(..., description="Duration of audio in seconds")
    word_count: int = Field(..., description="Number of words in transcript")
    extracted_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Hello everyone, today we're discussing...",
                "duration_seconds": 3600.0,
                "word_count": 5000,
                "extracted_at": "2026-03-20T10:30:00"
            }
        }


class FrameAnalysis(BaseModel):
    """Analysis of a single frame from the video."""
    frame_number: int = Field(..., description="Frame number in sequence")
    timestamp_seconds: float = Field(..., description="Timestamp in video where frame appears")
    image_path: str = Field(..., description="Path to the extracted frame image")
    description: str = Field(..., description="AI-generated description of the frame")

    class Config:
        json_schema_extra = {
            "example": {
                "frame_number": 1,
                "timestamp_seconds": 0.0,
                "image_path": "frames/frame_0001.jpg",
                "description": "A person presenting slides in a conference room."
            }
        }


class Summary(BaseModel):
    """Complete analysis summary for a video."""
    title: Optional[str] = Field(None, description="Generated title for the video")
    summary: str = Field(..., description="Comprehensive summary of video content")
    key_points: list[str] = Field(default_factory=list, description="Main points discussed")
    topics: list[str] = Field(default_factory=list, description="Topics covered")
    action_items: list[str] = Field(default_factory=list, description="Actionable items or conclusions")
    duration_seconds: float = Field(..., description="Total video duration in seconds")
    transcript_word_count: int = Field(..., description="Word count of transcript")
    frames_analyzed: int = Field(..., description="Number of frames analyzed")
    generated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Conference Keynote on AI Advances",
                "summary": "The speaker discussed recent breakthroughs in AI...",
                "key_points": ["Point 1", "Point 2"],
                "topics": ["AI", "Machine Learning"],
                "action_items": ["Follow up on X", "Research Y"],
                "duration_seconds": 3600.0,
                "transcript_word_count": 5000,
                "frames_analyzed": 60,
                "generated_at": "2026-03-20T10:35:00"
            }
        }


class ProcessingConfig(BaseModel):
    """Configuration for video processing."""
    fps: float = Field(default=1.0, description="Frames per second to extract")
    max_frames: Optional[int] = Field(None, description="Maximum number of frames to analyze (None for all)")
    chunk_size: int = Field(default=2000, description="Token chunk size for transcription processing")
    keep_artifacts: bool = Field(default=False, description="Keep intermediate files after processing")
    output_formats: list[str] = Field(default=["json"], description="Output formats: json, markdown, text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "fps": 1.0,
                "max_frames": 100,
                "chunk_size": 2000,
                "keep_artifacts": False,
                "output_formats": ["json", "markdown"]
            }
        }


class ProcessingResult(BaseModel):
    """Complete result of video processing."""
    video_path: str = Field(..., description="Path to input video")
    transcript: Transcript = Field(..., description="Extracted transcript")
    frame_analyses: list[FrameAnalysis] = Field(default_factory=list, description="Analysis of extracted frames")
    summary: Summary = Field(..., description="Generated summary")
    processing_time_seconds: float = Field(..., description="Total processing time in seconds")
    output_paths: dict[str, str] = Field(default_factory=dict, description="Paths to output files (json, markdown, text)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "video_path": "input.mp4",
                "transcript": {},
                "frame_analyses": [],
                "summary": {},
                "processing_time_seconds": 120.5,
                "output_paths": {
                    "json": "output.json",
                    "markdown": "output.md",
                    "text": "output.txt"
                }
            }
        }
