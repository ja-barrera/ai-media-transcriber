"""
CLI for AI Media Transcriber.
Process videos to extract transcripts, visual analysis, and summaries.
"""
import sys
from pathlib import Path
from typing import Optional

import typer

from .config import settings
from .logger import setup_logger
from .types import ProcessingConfig
from .pipeline import VideoAnalysisPipeline
from .formatters import OutputFormatter

logger = setup_logger(__name__, level=settings.log_level)

app = typer.Typer(
    name="amt",
    help="AI Media Transcriber - Analyze and summarize videos with AI"
)


@app.command()
def process(
    video_path: str = typer.Argument(
        ...,
        help="Path to the video file to analyze"
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
    fps: float = typer.Option(
        1.0,
        "--fps",
        help="Frames per second to extract from video"
    ),
    max_frames: Optional[int] = typer.Option(
        None,
        "--max-frames",
        "-m",
        help="Maximum number of frames to analyze (None for all)"
    ),
    keep_artifacts: bool = typer.Option(
        False,
        "--keep-artifacts",
        "-k",
        help="Keep intermediate files (audio, frames, transcript) after processing"
    ),
    api_key: Optional[str] = typer.Option(
        None,
        "--api-key",
        help="OpenAI API key (uses environment variable if not provided)",
        envvar="OPENAI_API_KEY"
    ),
):
    """
    Process a video file through the complete analysis pipeline.
    
    Extracts audio, transcribes speech, analyzes visual frames, and generates a summary.
    
    Example:
        amt process video.mp4 --output-format all --keep-artifacts
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
        
        # Create processing configuration
        config = ProcessingConfig(
            fps=fps,
            max_frames=max_frames,
            keep_artifacts=keep_artifacts,
            output_formats=formats
        )
        
        # Create pipeline and process
        typer.echo("🎬 Starting AI Media Transcriber...")
        typer.echo(f"📹 Video: {video_path}")
        typer.echo("")
        
        pipeline = VideoAnalysisPipeline(openai_api_key=api_key)
        result = pipeline.process_video(
            video_path=video_path,
            config=config,
            output_dir=output_dir
        )
        
        # Save outputs
        typer.echo("")
        typer.echo("💾 Saving results...")
        output_paths = OutputFormatter.format_and_save(
            result=result,
            output_dir=output_dir,
            formats=formats
        )
        
        # Display results summary
        typer.echo("")
        typer.echo("=" * 60)
        typer.echo("✅ Analysis completed successfully!")
        typer.echo("=" * 60)
        typer.echo("")
        typer.echo(f"📊 Summary: {result.summary.title}")
        typer.echo(f"⏱️ Duration: {result.summary.duration_seconds:.1f} seconds")
        typer.echo(f"📝 Transcript: {result.summary.transcript_word_count} words")
        typer.echo(f"🖼️  Frames analyzed: {result.summary.frames_analyzed}")
        typer.echo(f"⚡ Processing time: {result.processing_time_seconds:.1f} seconds")
        typer.echo("")
        typer.echo("📁 Output files:")
        for format_name, file_path in output_paths.items():
            typer.echo(f"  • {format_name.upper()}: {file_path}")
        
        if keep_artifacts:
            typer.echo("")
            typer.echo("📂 Intermediate files preserved (use --keep-artifacts to control)")
        
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        logger.exception("Pipeline failed")
        raise typer.Exit(code=1)


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
