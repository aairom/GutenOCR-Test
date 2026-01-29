# docling_gutenocr_combined.py
"""
Combined Docling + GutenOCR Application
Integrates Docling's document processing with GutenOCR's OCR capabilities
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    logging.warning("Docling not available. Install with: pip install docling")

from gutenocr_engine import GutenOCREngine
from file_processor import FileProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DoclingGutenOCRProcessor:
    """
    Combined processor using Docling for document structure and GutenOCR for OCR
    """
    
    def __init__(
        self,
        gutenocr_model: str = "rootsautomation/GutenOCR-3B",
        use_cpu: bool = False,
        use_docling: bool = True
    ):
        """
        Initialize combined processor
        
        Args:
            gutenocr_model: GutenOCR model to use
            use_cpu: Force CPU usage
            use_docling: Whether to use Docling (if available)
        """
        # Initialize GutenOCR
        self.gutenocr = GutenOCREngine(
            model_id=gutenocr_model,
            use_cpu=use_cpu
        )
        
        # Initialize Docling if available and requested
        self.use_docling = use_docling and DOCLING_AVAILABLE
        if self.use_docling:
            try:
                pipeline_options = PdfPipelineOptions()
                pipeline_options.do_ocr = False  # We'll use GutenOCR for OCR
                pipeline_options.do_table_structure = True
                
                self.docling_converter = DocumentConverter(
                    allowed_formats=[
                        InputFormat.PDF,
                        InputFormat.DOCX,
                        InputFormat.PPTX,
                        InputFormat.IMAGE,
                        InputFormat.HTML,
                        InputFormat.MD
                    ],
                    pdf_backend=PyPdfiumDocumentBackend,
                    pipeline_options=pipeline_options
                )
                logger.info("Docling initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize Docling: {e}")
                self.use_docling = False
        else:
            self.docling_converter = None
            if not DOCLING_AVAILABLE:
                logger.warning("Docling not available - using GutenOCR only")
        
        self.file_processor = FileProcessor()
    
    def process_document(
        self,
        file_path: str,
        extract_structure: bool = True,
        extract_tables: bool = True,
        ocr_images: bool = True
    ) -> Dict[str, Any]:
        """
        Process a document with combined Docling + GutenOCR
        
        Args:
            file_path: Path to document
            extract_structure: Extract document structure with Docling
            extract_tables: Extract tables with Docling
            ocr_images: Perform OCR on images with GutenOCR
        
        Returns:
            Combined processing results
        """
        result = {
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "docling_structure": None,
            "gutenocr_ocr": None,
            "combined_text": "",
            "metadata": {}
        }
        
        try:
            # Step 1: Process with Docling if available
            if self.use_docling and extract_structure:
                logger.info(f"Processing with Docling: {file_path}")
                docling_result = self._process_with_docling(
                    file_path,
                    extract_tables=extract_tables
                )
                result["docling_structure"] = docling_result
                result["metadata"]["docling_processed"] = True
            
            # Step 2: Process with GutenOCR
            if ocr_images:
                logger.info(f"Processing with GutenOCR: {file_path}")
                ocr_result = self.gutenocr.process_image(
                    image_path=file_path,
                    task_type="reading",
                    output_format="TEXT2D"
                )
                result["gutenocr_ocr"] = ocr_result
                result["metadata"]["gutenocr_processed"] = True
                
                if ocr_result.get("success"):
                    result["combined_text"] = ocr_result.get("text", "")
            
            # Step 3: Combine results
            if result["docling_structure"] and result["gutenocr_ocr"]:
                result["combined_text"] = self._merge_results(
                    result["docling_structure"],
                    result["gutenocr_ocr"]
                )
                result["metadata"]["processing_mode"] = "combined"
            elif result["docling_structure"]:
                result["combined_text"] = result["docling_structure"].get("text", "")
                result["metadata"]["processing_mode"] = "docling_only"
            elif result["gutenocr_ocr"]:
                result["combined_text"] = result["gutenocr_ocr"].get("text", "")
                result["metadata"]["processing_mode"] = "gutenocr_only"
            
            result["success"] = True
            
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def _process_with_docling(
        self,
        file_path: str,
        extract_tables: bool = True
    ) -> Dict[str, Any]:
        """Process document with Docling"""
        try:
            conv_result = self.docling_converter.convert(file_path)
            
            # Extract document structure
            doc_result = {
                "text": conv_result.document.export_to_markdown(),
                "structure": {
                    "pages": len(conv_result.document.pages) if hasattr(conv_result.document, 'pages') else 0,
                    "elements": []
                },
                "tables": [],
                "metadata": conv_result.document.metadata if hasattr(conv_result.document, 'metadata') else {}
            }
            
            # Extract tables if requested
            if extract_tables and hasattr(conv_result.document, 'tables'):
                for table in conv_result.document.tables:
                    doc_result["tables"].append({
                        "data": table.export_to_dataframe().to_dict() if hasattr(table, 'export_to_dataframe') else {},
                        "caption": getattr(table, 'caption', '')
                    })
            
            return doc_result
            
        except Exception as e:
            logger.error(f"Docling processing error: {e}")
            return {"error": str(e)}
    
    def _merge_results(
        self,
        docling_result: Dict[str, Any],
        gutenocr_result: Dict[str, Any]
    ) -> str:
        """
        Merge Docling structure with GutenOCR OCR results
        
        Args:
            docling_result: Docling processing result
            gutenocr_result: GutenOCR processing result
        
        Returns:
            Merged text content
        """
        merged_text = []
        
        # Add Docling structured content
        if docling_result.get("text"):
            merged_text.append("=== DOCUMENT STRUCTURE (Docling) ===\n")
            merged_text.append(docling_result["text"])
            merged_text.append("\n")
        
        # Add tables if present
        if docling_result.get("tables"):
            merged_text.append("\n=== EXTRACTED TABLES ===\n")
            for idx, table in enumerate(docling_result["tables"], 1):
                merged_text.append(f"\nTable {idx}:")
                if table.get("caption"):
                    merged_text.append(f"Caption: {table['caption']}")
                merged_text.append(str(table.get("data", {})))
                merged_text.append("\n")
        
        # Add GutenOCR OCR content
        if gutenocr_result.get("success") and gutenocr_result.get("text"):
            merged_text.append("\n=== OCR CONTENT (GutenOCR) ===\n")
            merged_text.append(gutenocr_result["text"])
        
        return "\n".join(merged_text)
    
    def batch_process(
        self,
        input_dir: str = "./input",
        output_dir: str = "./output",
        extract_structure: bool = True,
        extract_tables: bool = True,
        ocr_images: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Batch process documents
        
        Args:
            input_dir: Input directory
            output_dir: Output directory
            extract_structure: Extract structure with Docling
            extract_tables: Extract tables
            ocr_images: Perform OCR
        
        Returns:
            List of processing results
        """
        # Update file processor directories
        self.file_processor.input_dir = Path(input_dir)
        self.file_processor.output_dir = Path(output_dir)
        
        # Discover files
        files = self.file_processor.discover_images(recursive=True)
        
        results = []
        for file_path in files:
            logger.info(f"Processing: {file_path}")
            result = self.process_document(
                file_path,
                extract_structure=extract_structure,
                extract_tables=extract_tables,
                ocr_images=ocr_images
            )
            results.append(result)
        
        # Save results
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"combined_results_{timestamp_str}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {output_path}")
        
        return results
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get information about available capabilities"""
        return {
            "docling_available": self.use_docling,
            "gutenocr_model": self.gutenocr.model_id,
            "device_info": self.gutenocr.get_device_info(),
            "supported_formats": [
                "PDF", "DOCX", "PPTX", "PNG", "JPG", "JPEG",
                "TIFF", "BMP", "GIF", "WEBP", "HTML", "MD"
            ] if self.use_docling else [
                "PNG", "JPG", "JPEG", "TIFF", "BMP", "GIF", "WEBP", "PDF"
            ]
        }


def main():
    """Main entry point for combined processor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Combined Docling + GutenOCR Processor")
    parser.add_argument("--input", default="./input", help="Input directory")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--model", default="rootsautomation/GutenOCR-3B", help="GutenOCR model")
    parser.add_argument("--cpu", action="store_true", help="Force CPU usage")
    parser.add_argument("--no-docling", action="store_true", help="Disable Docling")
    parser.add_argument("--no-structure", action="store_true", help="Skip structure extraction")
    parser.add_argument("--no-tables", action="store_true", help="Skip table extraction")
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = DoclingGutenOCRProcessor(
        gutenocr_model=args.model,
        use_cpu=args.cpu,
        use_docling=not args.no_docling
    )
    
    # Print capabilities
    capabilities = processor.get_capabilities()
    print("\n=== Processor Capabilities ===")
    for key, value in capabilities.items():
        print(f"{key}: {value}")
    print()
    
    # Process documents
    results = processor.batch_process(
        input_dir=args.input,
        output_dir=args.output,
        extract_structure=not args.no_structure,
        extract_tables=not args.no_tables,
        ocr_images=not args.no_ocr
    )
    
    # Print summary
    successful = sum(1 for r in results if r.get("success"))
    print(f"\n=== Processing Complete ===")
    print(f"Total files: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")


if __name__ == "__main__":
    main()

# Made with Bob
