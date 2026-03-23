# AI Media Transcriber

A Python CLI tool that analyzes and summarizes videos using OpenAI APIs. Extract transcripts, analyze visual content, and generate comprehensive summaries—all from your command line.

## Features

- **Audio Extraction**: Extract audio from video files using FFmpeg
- **Speech Recognition**: Transcribe audio using OpenAI's Whisper API
- **Visual Analysis**: Analyze video frames using GPT-4V vision model
- **Intelligent Summarization**: Generate structured summaries with key points and action items
- **Multiple Output Formats**: Export results as JSON, Markdown, or plain text
- **Artifact Management**: Option to keep intermediate files for inspection/reprocessing

## Installation

### Prerequisites

- Python 3.12+
- OpenAI API key (get one from [platform.openai.com](https://platform.openai.com))
- FFmpeg (for video/audio processing)

### Install FFmpeg

**Windows (using Chocolatey):**
```bash
choco install ffmpeg
```

**macOS (using Homebrew):**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

### Install AI Media Transcriber

```bash
# Clone the repository
git clone https://github.com/ja-barrera/ai-media-transcriber.git
cd ai-media-transcriber

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install the tool
pip install -e .
```

## Configuration

### Set Your OpenAI API Key

Create a `.env` file in the project directory:

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
export OPENAI_API_KEY='sk-your-api-key-here'
```

Or set it directly as an environment variable:

```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

You can also use the `--api-key` option when running commands:

```bash
amt process video.mp4 --api-key sk-your-api-key-here
```

## Usage

### Basic Usage

Analyze a video with default settings:

```bash
amt process video.mp4
```

This will:
1. Extract audio from the video
2. Transcribe the audio using Whisper
3. Extract frames at 1 fps and analyze them with GPT-4V
4. Generate a summary using GPT-4
5. Save results to `output/` directory in JSON format

### Advanced Options

```bash
amt process video.mp4 \
  --output-format all \              # Save as JSON, Markdown, and text
  --output-dir ./results \           # Custom output directory
  --fps 2.0 \                        # Extract 2 frames per second
  --max-frames 50 \                  # Limit to 50 frames maximum
  --keep-artifacts                   # Preserve intermediate files
```

### Output Formats

**JSON** - Machine-readable format with all metadata:
```bash
amt process video.mp4 --output-format json
```

**Markdown** - Formatted for reading and documentation:
```bash
amt process video.mp4 --output-format markdown
```

**Text** - Clean, readable plain text:
```bash
amt process video.mp4 --output-format text
```

**All** - Save in all three formats:
```bash
amt process video.mp4 --output-format all
```

### Keep Intermediate Files

By default, temporary files (audio.wav, frames/) are deleted after processing. To keep them:

```bash
amt process video.mp4 --keep-artifacts
```

This saves temporary files in a `.amt_tmp/` directory for inspection or reprocessing.

## Command Reference

### `amt process`

Analyze a video file.

```
Usage: amt process [OPTIONS] VIDEO_PATH

Arguments:
  VIDEO_PATH  Path to the video file to analyze

Options:
  -o, --output-dir TEXT        Directory where results will be saved [default: output]
  -f, --output-format FORMAT   Output format: json, markdown, text, or all [default: json]
  --fps FLOAT                  Frames per second to extract [default: 1.0]
  -m, --max-frames INTEGER     Maximum frames to analyze
  -k, --keep-artifacts         Keep intermediate files (audio, frames, transcript)
  --api-key TEXT              OpenAI API key (uses environment variable if not set)
  --help                       Show help message
```

### `amt version`

Show version information.

```bash
amt version
```

### `amt info`

Show configuration and environment information.

```bash
amt info
```

## Examples

### Example 1: Quick Analysis with Default Settings

```bash
amt process conference_talk.mp4
```

Creates `output/conference_talk_analysis.json` with summary and metadata.

### Example 2: Full Analysis with All Outputs

```bash
amt process tutorial.mp4 --output-format all --keep-artifacts
```

Saves:
- `output/tutorial_analysis.json`
- `output/tutorial_analysis.md`
- `output/tutorial_analysis.txt`
- Intermediate files in `.amt_tmp/`

### Example 3: Sample More Frames from a Long Video

```bash
amt process long_webinar.mp4 --fps 2.0 --max-frames 100
```

Extracts 2 frames per second but limits to 100 total frames for analysis.

### Example 4: Custom Output Directory

```bash
amt process video.mp4 --output-dir ./analysis/results
```

Saves results to `./analysis/results/video_analysis.*`

## Output Structure

### JSON Format

```json
{
  "video_path": "input.mp4",
  "processing_time_seconds": 120.5,
  "transcript": {
    "text": "Full transcription text...",
    "duration_seconds": 3600.0,
    "word_count": 5500
  },
  "frames_analyzed": 60,
  "summary": {
    "title": "Video Title",
    "summary": "Comprehensive summary text...",
    "key_points": ["Point 1", "Point 2"],
    "topics": ["Topic A", "Topic B"],
    "action_items": ["Action 1", "Action 2"]
  }
}
```

### Markdown Format

The Markdown output includes:
- Title and metadata
- Summary section
- Key points (bulleted)
- Topics covered
- Action items
- Full transcript
- Visual scene descriptions

### Text Format

A formatted plain text version suitable for reading, printing, or sharing.

## Configuration File

Edit `.env` to customize default behavior:

```ini
# OpenAI Models
AMT_OPENAI_MODEL_VISION=gpt-4-vision-preview
AMT_OPENAI_MODEL_SUMMARIZATION=gpt-4-turbo-preview

# Processing Defaults
AMT_DEFAULT_FPS=1.0
AMT_TRANSCRIPT_CHUNK_SIZE=2000

# Logging
AMT_LOG_LEVEL=INFO
```

See `.env.example` for all available options.

## Troubleshooting

### "FFmpeg not found"

Make sure FFmpeg is installed and in your PATH:

```bash
ffmpeg -version
ffprobe -version
```

### "OpenAI API key not found"

Set your API key:

```bash
export OPENAI_API_KEY='sk-...'
```

Or create a `.env` file with `AMT_OPENAI_API_KEY=sk-...`

### Rate Limiting (HTTP 429 errors)

The OpenAI API has rate limits. For long videos:
- Use `--max-frames` to limit frame analysis
- Space out requests with delays

### Large Video Files

For videos over 1 hour:
- Extracted audio will be large (can use significant disk space)
- Frame analysis will take time (especially with `--fps > 1`)
- Use `--max-frames` to sample strategically

## Architecture

The pipeline consists of four main stages:

1. **Audio Extraction** (FFmpeg) → WAV format
2. **Transcription** (Whisper API) → Full transcript
3. **Frame Analysis** (GPT-4V) → Scene descriptions
4. **Summarization** (GPT-4) → Structured summary

Results are formatted and saved in your chosen format(s).

## Development

### Running Tests

```bash
pytest tests/
```

### Code Structure

```
src/ai_media_transcriber/
├── config.py           # Configuration management
├── types.py            # Pydantic data models
├── logger.py           # Logging setup
├── ffmpeg_processor.py # Audio/frame extraction
├── openai_client.py    # OpenAI API wrappers
├── pipeline.py         # Main orchestrator
├── formatters.py       # Output formatting
├── file_utils.py       # File management
└── main.py             # CLI entry point
```

## Performance Notes

- **Transcription**: ~1-2 minutes per hour of video (Whisper API)
- **Frame Analysis**: ~5-10 seconds per frame (GPT-4V)
- **Summarization**: ~30 seconds (GPT-4)

Total time depends on video length and number of frames analyzed.

## Limitations

- Maximum file size depends on OpenAI API limits
- Vision analysis limited to ~100 frames recommended (adjust with `--max-frames`)
- Requires internet connection for OpenAI API calls

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or suggestions:
1. Check [GitHub Issues](https://github.com/ja-barrera/ai-media-transcriber/issues)
2. Create a new issue with detailed information
3. Include video format/length and error messages

## Acknowledgments

Built with:
- [OpenAI API](https://openai.com/api) - Whisper, GPT-4, GPT-4V
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [FFmpeg](https://ffmpeg.org/) - Media processing
