"""
File Processor - Handles recursive file discovery and output management
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileProcessor:
    """
    Handles file discovery and output management for OCR processing
    """
    
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp', '.pdf'}
    
    def __init__(self, input_dir: str = "./input", output_dir: str = "./output"):
        """
        Initialize FileProcessor
        
        Args:
            input_dir: Directory to scan for images
            output_dir: Directory to save results
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_images(self, recursive: bool = True) -> List[str]:
        """
        Discover all supported image files in input directory
        
        Args:
            recursive: Whether to search recursively
        
        Returns:
            List of image file paths
        """
        image_files = []
        
        if recursive:
            for ext in self.SUPPORTED_EXTENSIONS:
                image_files.extend(self.input_dir.rglob(f"*{ext}"))
                image_files.extend(self.input_dir.rglob(f"*{ext.upper()}"))
        else:
            for ext in self.SUPPORTED_EXTENSIONS:
                image_files.extend(self.input_dir.glob(f"*{ext}"))
                image_files.extend(self.input_dir.glob(f"*{ext.upper()}"))
        
        # Convert to strings and sort
        image_files = sorted([str(f) for f in image_files])
        
        logger.info(f"Discovered {len(image_files)} image files")
        return image_files
    
    def save_results(
        self,
        results: List[Dict[str, Any]],
        format: str = "json",
        timestamp: bool = True
    ) -> str:
        """
        Save OCR results to output directory
        
        Args:
            results: List of OCR results
            format: Output format ('json', 'txt', 'csv')
            timestamp: Whether to include timestamp in filename
        
        Returns:
            Path to saved file
        """
        # Generate filename with timestamp
        if timestamp:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ocr_results_{timestamp_str}"
        else:
            filename = "ocr_results"
        
        if format == "json":
            output_path = self.output_dir / f"{filename}.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        
        elif format == "txt":
            output_path = self.output_dir / f"{filename}.txt"
            with open(output_path, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(f"{'='*80}\n")
                    f.write(f"File: {result.get('image_path', 'Unknown')}\n")
                    f.write(f"Status: {'Success' if result.get('success') else 'Failed'}\n")
                    if result.get('success'):
                        f.write(f"Text:\n{result.get('text', '')}\n")
                    else:
                        f.write(f"Error: {result.get('error', 'Unknown error')}\n")
                    f.write(f"{'='*80}\n\n")
        
        elif format == "csv":
            import csv
            output_path = self.output_dir / f"{filename}.csv"
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                if results:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)
        
        logger.info(f"Results saved to: {output_path}")
        return str(output_path)
    
    def save_individual_results(
        self,
        results: List[Dict[str, Any]],
        format: str = "txt"
    ) -> List[str]:
        """
        Save individual result files for each processed image
        
        Args:
            results: List of OCR results
            format: Output format ('txt', 'json')
        
        Returns:
            List of saved file paths
        """
        saved_files = []
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for idx, result in enumerate(results):
            # Generate filename based on original image
            image_path = Path(result.get('image_path', f'image_{idx}'))
            base_name = image_path.stem
            
            if format == "txt":
                output_path = self.output_dir / f"{base_name}_{timestamp_str}.txt"
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Source: {result.get('image_path', 'Unknown')}\n")
                    f.write(f"Processed: {datetime.now().isoformat()}\n")
                    f.write(f"Task: {result.get('task_type', 'Unknown')}\n")
                    f.write(f"Format: {result.get('output_format', 'Unknown')}\n")
                    f.write(f"\n{'='*80}\n\n")
                    if result.get('success'):
                        f.write(result.get('text', ''))
                    else:
                        f.write(f"Error: {result.get('error', 'Unknown error')}")
            
            elif format == "json":
                output_path = self.output_dir / f"{base_name}_{timestamp_str}.json"
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            
            saved_files.append(str(output_path))
            logger.info(f"Saved individual result: {output_path}")
        
        return saved_files
    
    def get_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate statistics from OCR results
        
        Args:
            results: List of OCR results
        
        Returns:
            Dictionary with statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r.get('success'))
        failed = total - successful
        
        total_chars = sum(len(r.get('text', '')) for r in results if r.get('success'))
        avg_chars = total_chars / successful if successful > 0 else 0
        
        return {
            "total_images": total,
            "successful": successful,
            "failed": failed,
            "success_rate": f"{(successful/total*100):.2f}%" if total > 0 else "0%",
            "total_characters": total_chars,
            "average_characters_per_image": f"{avg_chars:.2f}",
            "timestamp": datetime.now().isoformat()
        }
    
    def create_summary_report(
        self,
        results: List[Dict[str, Any]],
        statistics: Dict[str, Any]
    ) -> str:
        """
        Create a summary report of the OCR processing
        
        Args:
            results: List of OCR results
            statistics: Statistics dictionary
        
        Returns:
            Path to summary report
        """
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"summary_report_{timestamp_str}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("GutenOCR Processing Summary Report\n")
            f.write("="*80 + "\n\n")
            
            f.write("Statistics:\n")
            f.write("-" * 40 + "\n")
            for key, value in statistics.items():
                f.write(f"{key.replace('_', ' ').title()}: {value}\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("Detailed Results:\n")
            f.write("="*80 + "\n\n")
            
            for idx, result in enumerate(results, 1):
                f.write(f"{idx}. {Path(result.get('image_path', 'Unknown')).name}\n")
                f.write(f"   Status: {'✓ Success' if result.get('success') else '✗ Failed'}\n")
                if not result.get('success'):
                    f.write(f"   Error: {result.get('error', 'Unknown')}\n")
                f.write("\n")
        
        logger.info(f"Summary report saved to: {report_path}")
        return str(report_path)

# Made with Bob
