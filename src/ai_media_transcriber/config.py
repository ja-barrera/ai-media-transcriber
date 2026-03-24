"""
Configuration management for AI Media Transcriber.
Loads settings from environment variables and provides defaults.
"""
import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    def __init__(self):
        # Load from environment variables, with defaults
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AMT_OPENAI_API_KEY", "")
        self.openai_model_transcription = os.getenv("AMT_OPENAI_MODEL_TRANSCRIPTION", "gpt-4o-mini-transcribe")
        self.openai_model_vision = os.getenv("AMT_OPENAI_MODEL_VISION", "gpt-5.4-nano")
        self.openai_model_summarization = os.getenv("AMT_OPENAI_MODEL_SUMMARIZATION", "gpt-5.4-nano")
        self.openai_temperature = float(os.getenv("AMT_OPENAI_TEMPERATURE", "0.3"))
        self.openai_max_tokens_summary = int(os.getenv("AMT_OPENAI_MAX_TOKENS_SUMMARY", "2000"))
        self.openai_timeout = int(os.getenv("AMT_OPENAI_TIMEOUT", "60"))
        
        # FFmpeg configuration
        self.ffmpeg_audio_sample_rate = int(os.getenv("AMT_FFMPEG_AUDIO_SAMPLE_RATE", "16000"))
        self.ffmpeg_audio_channels = int(os.getenv("AMT_FFMPEG_AUDIO_CHANNELS", "1"))
        self.ffmpeg_audio_codec = os.getenv("AMT_FFMPEG_AUDIO_CODEC", "pcm_s16le")
        
        # Processing defaults
        self.default_fps = float(os.getenv("AMT_DEFAULT_FPS", "10.0"))
        self.max_frames_per_video = None
        max_frames_str = os.getenv("AMT_MAX_FRAMES_PER_VIDEO")
        if max_frames_str:
            self.max_frames_per_video = int(max_frames_str)
        
        self.transcript_chunk_size = int(os.getenv("AMT_TRANSCRIPT_CHUNK_SIZE", "2000"))
        
        # Output configuration
        default_formats = os.getenv("AMT_DEFAULT_OUTPUT_FORMATS", "json")
        self.default_output_formats = [f.strip() for f in default_formats.split(",")]
        self.keep_artifacts_by_default = os.getenv("AMT_KEEP_ARTIFACTS_BY_DEFAULT", "false").lower() == "true"
        
        # Temporary files
        self.temp_dir_base = os.getenv("AMT_TEMP_DIR_BASE", ".amt_tmp")
        
        # Logging
        self.log_level = os.getenv("AMT_LOG_LEVEL", "INFO")
    
    def validate_api_key(self) -> bool:
        """Check if OpenAI API key is configured."""
        return bool(self.openai_api_key.strip())
    
    def get_temp_dir(self, video_name: str) -> str:
        """Generate temporary directory path for a video."""
        import hashlib
        video_hash = hashlib.md5(video_name.encode()).hexdigest()[:8]
        return os.path.join(self.temp_dir_base, video_hash)


# Global settings instance (instantiate on module load)
settings = Settings()

# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        # Reload settings after loading .env
        global settings
        settings = Settings()

# Try to load .env file on module import
try:
    load_env_file()
except Exception:
    pass  # Silently ignore if .env doesn't exist
