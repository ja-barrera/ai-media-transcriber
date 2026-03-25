"""
CLI for AI Media Transcriber.
Process videos, images, or audio files to extract insights and generate summaries.
"""
import os
from pathlib import Path
from typing import Optional

import typer

from .config import settings
from .logger import setup_logger
from .types import ProcessingConfig
from .pipeline import MediaAnalysisPipeline
from .formatters import OutputFormatter
from .file_detector import detect_file_type, FileType

logger = setup_logger(__name__, level=settings.log_level)

app = typer.Typer(
    name="amt",
    help="AI Media Transcriber - Analyze videos, images, and audio with AI"
)


@app.command()
def process(
    file_path: str = typer.Argument(
        ...,
        help="Path to the video, image, or audio file to analyze. For batch images, provide the first image and use --batch option."
    ),
    output_dir: str = typer.Option(
        "output",
        "--output-dir",
        "-o",
        help="Directory where results will be saved"
    ),
    output_format: str = typer.Option(
        "json",
        "--output-format",
        "-f",
        help="Output format(s): json, markdown, text, or all",
        metavar="FORMAT"
    ),
    fps: Optional[float] = typer.Option(
        None,
        "--fps",
        help="Frames per second to extract from video (video only)"
    ),
    max_frames: Optional[int] = typer.Option(
        None,
        "--max-frames",
        "-m",
        help="Maximum number of frames to analyze (video only)"
    ),
    keep_artifacts: bool = typer.Option(
        False,
        "--keep-artifacts",
        "-k",
        help="Keep intermediate files after processing"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="OpenAI API key (uses environment variable if not provided)",
        envvar="OPENAI_API_KEY"
    ),
    batch_images: Optional[str] = typer.Option(
        None,
        "--batch",
        help="Comma-separated paths for batch image processing (image files only)"
    ),
):
    """
    Process a video, image, or audio file through the analysis pipeline.
    
    Auto-detects file type and applies appropriate analysis:
    - VIDEO: Extracts audio, transcribes, analyzes frames, generates summary
    - IMAGE: Analyzes with vision model and generates description
    - AUDIO: Transcribes speech and generates summary
    
    Examples:
        amt process video.mp4 --output-format all
        amt process photo.jpg
        amt process podcast.mp3 --output-format markdown
        amt process photo1.jpg --batch photo2.jpg,photo3.jpg
    """
    try:
        # Validate API key
        api_key = api_key or settings.openai_api_key
        if not api_key:
            typer.echo(
                "Error: OpenAI API key not found. "
                "Set OPENAI_API_KEY environment variable or use --api-key option",
                err=True
            )
            raise typer.Exit(code=1)
        
        # Validate output format
        valid_formats = {'json', 'markdown', 'text', 'all'}
        if output_format.lower() not in valid_formats:
            typer.echo(
                f"Error: Invalid output format '{output_format}'. "
                f"Valid options: {', '.join(valid_formats)}",
                err=True
            )
            raise typer.Exit(code=1)
        
        # Determine output formats
        if output_format.lower() == 'all':
            formats = ['json', 'markdown', 'text']
        else:
            formats = [output_format.lower()]
        
        # Detect file type
        file_type = detect_file_type(file_path)
        
        # Create pipeline
        pipeline = MediaAnalysisPipeline(openai_api_key=api_key)
        
        # Route to appropriate processor
        if file_type == FileType.VIDEO:
            _process_video(pipeline, file_path, output_dir, formats, fps, max_frames, keep_artifacts)
        elif file_type == FileType.IMAGE:
            if batch_images:
                # Batch image processing
                image_paths = [file_path] + [p.strip() for p in batch_images.split(',')]
                _process_images_batch(pipeline, image_paths, output_dir, formats)
            else:
                # Single image
                _process_single_image(pipeline, file_path, output_dir, formats)
        elif file_type == FileType.AUDIO:
            _process_audio(pipeline, file_path, output_dir, formats)
        else:
            typer.echo(
                f"Error: Unsupported file type '{Path(file_path).suffix}'. "
                "Supported: video (mp4, mkv, avi, mov), image (jpg, png, gif, webp), audio (mp3, wav, m4a, aac)",
                err=True
            )
            raise typer.Exit(code=1)
    
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Processing failed")
        raise typer.Exit(code=1)


def _process_video(pipeline, video_path, output_dir, formats, fps, max_frames, keep_artifacts):
    """Process a video file."""
    config = ProcessingConfig(
        fps=fps or settings.default_fps,
        max_frames=max_frames,
        keep_artifacts=keep_artifacts,
        output_formats=formats
    )
    
    typer.echo("🎬 Starting video analysis...")
    typer.echo(f"📹 Video: {video_path}")
    typer.echo("")
    
    result = pipeline.process_video(video_path, config, output_dir)
    
    # Save outputs
    typer.echo("")
    typer.echo("💾 Saving results...")
    output_paths = OutputFormatter.format_and_save(result, output_dir, formats)
    
    # Display summary
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("✅ Video analysis completed!")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo(f"📊 {result.summary.title}")
    typer.echo(f"⏱️  Duration: {result.summary.duration_seconds:.1f}s")
    typer.echo(f"📝 Transcript: {result.summary.transcript_word_count} words")
    typer.echo(f"🖼️  Frames: {result.summary.frames_analyzed}")
    typer.echo(f"⚡ Time: {result.processing_time_seconds:.1f}s")
    typer.echo("")
    typer.echo("📁 Output files:")
    for fmt, path in output_paths.items():
        typer.echo(f"  • {fmt.upper()}: {path}")


def _process_single_image(pipeline, image_path, output_dir, formats):
    """Process a single image file."""
    typer.echo("🖼️  Starting image analysis...")
    typer.echo(f"📷 Image: {image_path}")
    typer.echo("")
    
    result = pipeline.process_images([image_path], output_dir)
    
    # Save outputs
    typer.echo("")
    typer.echo("💾 Saving results...")
    os.makedirs(output_dir, exist_ok=True)
    base_name = Path(image_path).stem
    output_paths = {}
    
    if 'json' in formats:
        json_path = os.path.join(output_dir, f"{base_name}_analysis.json")
        with open(json_path, 'w') as f:
            f.write(OutputFormatter.format_image_as_json(result))
        output_paths['json'] = json_path
    
    if 'markdown' in formats:
        md_path = os.path.join(output_dir, f"{base_name}_analysis.md")
        with open(md_path, 'w') as f:
            f.write(OutputFormatter.format_image_as_markdown(result))
        output_paths['markdown'] = md_path
    
    # Display summary
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("✅ Image analysis completed!")
    typer.echo("=" * 60)
    typer.echo("")
    if result.analyses:
        typer.echo(f"📊 Description:")
        typer.echo(result.analyses[0].description[:200] + "...")
    typer.echo("")
    typer.echo("📁 Output files:")
    for fmt, path in output_paths.items():
        typer.echo(f"  • {fmt.upper()}: {path}")


def _process_images_batch(pipeline, image_paths, output_dir, formats):
    """Process multiple images with consolidated summary."""
    typer.echo(f"🖼️  Starting batch image analysis ({len(image_paths)} images)...")
    for i, img in enumerate(image_paths, 1):
        typer.echo(f"  {i}. {img}")
    typer.echo("")
    
    result = pipeline.process_images(image_paths, output_dir)
    
    # Save outputs
    typer.echo("")
    typer.echo("💾 Saving results...")
    os.makedirs(output_dir, exist_ok=True)
    base_name = Path(image_paths[0]).stem + "_batch"
    output_paths = {}
    
    if 'json' in formats:
        json_path = os.path.join(output_dir, f"{base_name}_analysis.json")
        with open(json_path, 'w') as f:
            f.write(OutputFormatter.format_image_as_json(result))
        output_paths['json'] = json_path
    
    if 'markdown' in formats:
        md_path = os.path.join(output_dir, f"{base_name}_analysis.md")
        with open(md_path, 'w') as f:
            f.write(OutputFormatter.format_image_as_markdown(result))
        output_paths['markdown'] = md_path
    
    # Display summary
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("✅ Batch image analysis completed!")
    typer.echo("=" * 60)
    typer.echo("")
    if result.consolidated_summary:
        typer.echo(f"📊 Consolidated Summary:")
        summary_text = result.consolidated_summary.consolidated_summary
        typer.echo(summary_text[:300] + "..." if len(summary_text) > 300 else summary_text)
        if result.consolidated_summary.common_themes:
            typer.echo("")
            typer.echo("Common themes:")
            for theme in result.consolidated_summary.common_themes[:3]:
                typer.echo(f"  • {theme}")
    typer.echo(f"⚡ Time: {result.processing_time_seconds:.1f}s")
    typer.echo("")
    typer.echo("📁 Output files:")
    for fmt, path in output_paths.items():
        typer.echo(f"  • {fmt.upper()}: {path}")


def _process_audio(pipeline, audio_path, output_dir, formats):
    """Process an audio file."""
    typer.echo("🎵 Starting audio analysis...")
    typer.echo(f"🎧 Audio: {audio_path}")
    typer.echo("")
    
    result = pipeline.process_audio(audio_path, output_dir)
    
    # Save outputs
    typer.echo("")
    typer.echo("💾 Saving results...")
    os.makedirs(output_dir, exist_ok=True)
    base_name = Path(audio_path).stem
    output_paths = {}
    
    if 'json' in formats:
        json_path = os.path.join(output_dir, f"{base_name}_analysis.json")
        with open(json_path, 'w') as f:
            f.write(OutputFormatter.format_audio_as_json(result))
        output_paths['json'] = json_path
    
    if 'markdown' in formats:
        md_path = os.path.join(output_dir, f"{base_name}_analysis.md")
        with open(md_path, 'w') as f:
            f.write(OutputFormatter.format_audio_as_markdown(result))
        output_paths['markdown'] = md_path
    
    if 'text' in formats:
        txt_path = os.path.join(output_dir, f"{base_name}_analysis.txt")
        with open(txt_path, 'w') as f:
            f.write(OutputFormatter.format_audio_as_text(result))
        output_paths['text'] = txt_path
    
    # Display summary
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("✅ Audio analysis completed!")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo(f"📊 {result.summary.title}")
    typer.echo(f"⏱️  Duration: {result.transcript.duration_seconds:.1f}s")
    typer.echo(f"📝 Transcript: {result.transcript.word_count} words")
    typer.echo(f"⚡ Time: {result.processing_time_seconds:.1f}s")
    typer.echo("")
    typer.echo("📁 Output files:")
    for fmt, path in output_paths.items():
        typer.echo(f"  • {fmt.upper()}: {path}")


@app.command()
def version():
    """Show version information."""
    typer.echo("AI Media Transcriber v0.1.0")


@app.command()
def info():
    """Show configuration and environment information."""
    typer.echo("AI Media Transcriber - Configuration")
    typer.echo("=" * 50)
    typer.echo("")
    typer.echo("📋 Current Settings:")
    typer.echo(f"  OpenAI API Key configured: {bool(settings.openai_api_key)}")
    typer.echo(f"  Transcription model: {settings.openai_model_transcription}")
    typer.echo(f"  Vision model: {settings.openai_model_vision}")
    typer.echo(f"  Summarization model: {settings.openai_model_summarization}")
    typer.echo(f"  Default FPS: {settings.default_fps}")
    typer.echo(f"  Temp directory: {settings.temp_dir_base}")
    typer.echo("")
    typer.echo("💡 To use this tool, set your OpenAI API key:")
    typer.echo("  export OPENAI_API_KEY='sk-...'")
    typer.echo("")
    typer.echo("  Or create a .env file in the project directory with:")
    typer.echo("  AMT_OPENAI_API_KEY=sk-...")


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
