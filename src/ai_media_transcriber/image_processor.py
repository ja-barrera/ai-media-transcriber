"""
Image processing module.
Handles analysis of individual and batch images using OpenAI's vision API.
"""
import os
from pathlib import Path

from .config import settings
from .logger import setup_logger
from .types import ImageAnalysis, ConsolidatedImageSummary, ImageProcessingResult
from .openai_client import OpenAIClient

logger = setup_logger(__name__)


class ImageProcessor:
    """Process and analyze images using GPT-4V."""
    
    def __init__(self, openai_api_key: str = None):
        """
        Initialize the image processor.
        
        Args:
            openai_api_key: OpenAI API key
        """
        self.client = OpenAIClient(api_key=openai_api_key)
    
    def process_image(self, image_path: str) -> ImageAnalysis:
        """
        Analyze a single image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            ImageAnalysis object with description
        """
        image_path = str(image_path)
        
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        logger.info(f"Processing image: {image_path}")
        
        description = self.client.analyze_frame(image_path)
        
        analysis = ImageAnalysis(
            image_path=image_path,
            description=description
        )
        
        logger.info(f"✓ Image analysis completed")
        return analysis
    
    def process_images_batch(self, image_paths: list[str]) -> ImageProcessingResult:
        """
        Process multiple images and generate consolidated summary.
        
        Args:
            image_paths: List of paths to image files
        
        Returns:
            ImageProcessingResult with individual and consolidated summaries
        
        Raises:
            FileNotFoundError: If any image file not found
            Exception: If processing fails
        """
        import time
        start_time = time.time()
        
        logger.info(f"Processing {len(image_paths)} images")
        
        # Analyze each image
        analyses = []
        descriptions = []
        
        for idx, image_path in enumerate(image_paths, 1):
            try:
                logger.info(f"  Analyzing image {idx}/{len(image_paths)}...")
                analysis = self.process_image(image_path)
                analyses.append(analysis)
                descriptions.append(analysis.description)
            except Exception as e:
                logger.warning(f"  ✗ Failed to analyze image {idx}: {e}")
                continue
        
        if not analyses:
            raise Exception("Failed to analyze any images")
        
        logger.info(f"✓ Analyzed {len(analyses)} images")
        
        # Generate consolidated summary if multiple images
        consolidated_summary = None
        if len(analyses) > 1:
            logger.info("Generating consolidated summary...")
            consolidated_summary = self._generate_consolidated_summary(
                image_paths, descriptions
            )
        
        processing_time = time.time() - start_time
        
        return ImageProcessingResult(
            image_paths=image_paths,
            analyses=analyses,
            consolidated_summary=consolidated_summary,
            processing_time_seconds=processing_time
        )
    
    def _generate_consolidated_summary(
        self,
        image_paths: list[str],
        descriptions: list[str]
    ) -> ConsolidatedImageSummary:
        """
        Generate a consolidated summary combining all image descriptions.
        
        Args:
            image_paths: List of image paths
            descriptions: List of individual descriptions
        
        Returns:
            ConsolidatedImageSummary
        """
        # Combine descriptions into context
        combined_descriptions = "\n".join(
            f"Image {i+1}: {desc}"
            for i, desc in enumerate(descriptions)
        )
        
        # Generate consolidated summary
        context = (
            f"I have analyzed {len(image_paths)} images. Here are the descriptions:\n\n"
            f"{combined_descriptions}\n\n"
            f"Please provide:\n"
            f"1. A consolidated summary that ties together insights from all images\n"
            f"2. Common themes that appear across the images\n"
            f"Keep the summary concise (2-3 paragraphs) and the themes as a bullet list."
        )
        
        summary_dict = self.client.summarize(context)
        
        return ConsolidatedImageSummary(
            consolidated_summary=summary_dict.get('summary', ''),
            common_themes=summary_dict.get('topics', []),
            image_count=len(image_paths)
        )
