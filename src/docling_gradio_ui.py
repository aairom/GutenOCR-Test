# docling_gradio_ui.py
"""
Docling + GutenOCR Combined Gradio UI
A dedicated web interface for combined document processing
"""
import os
import json
import gradio as gr
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

from docling_gutenocr_combined import DoclingGutenOCRProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DoclingGutenOCRUI:
    """Gradio UI for Docling + GutenOCR combined processing"""
    
    def __init__(self):
        self.processor: Optional[DoclingGutenOCRProcessor] = None
        self.input_dir = Path("./input")
        self.output_dir = Path("./output")
        
        # Ensure directories exist
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def initialize_processor(
        self,
        model_choice: str,
        use_cpu: bool,
        use_docling: bool,
        progress=gr.Progress()
    ) -> str:
        """Initialize the combined processor"""
        try:
            progress(0.1, desc="Initializing processor...")
            
            model_id = "rootsautomation/GutenOCR-3B" if model_choice == "GutenOCR-3B" else "rootsautomation/GutenOCR-7B"
            
            progress(0.3, desc=f"Loading {model_choice}...")
            self.processor = DoclingGutenOCRProcessor(
                gutenocr_model=model_id,
                use_cpu=use_cpu,
                use_docling=use_docling
            )
            
            progress(0.9, desc="Getting capabilities...")
            capabilities = self.processor.get_capabilities()
            
            progress(1.0, desc="Complete!")
            
            return f"""✅ Processor initialized successfully!

**Configuration:**
- Model: {model_choice}
- Device: {'CPU' if use_cpu else 'GPU'}
- Docling: {'Enabled' if capabilities['docling_available'] else 'Disabled'}

**Capabilities:**
- Supported formats: {', '.join(capabilities['supported_formats'])}
- Device info: {capabilities['device_info']}
"""
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return f"❌ Error: {str(e)}"
    
    def process_single_document(
        self,
        file,
        extract_structure: bool,
        extract_tables: bool,
        ocr_images: bool,
        progress=gr.Progress()
    ) -> tuple:
        """Process a single document"""
        if self.processor is None:
            return "❌ Please initialize the processor first!", None, None
        
        if file is None:
            return "❌ Please upload a file!", None, None
        
        try:
            progress(0.1, desc="Processing document...")
            
            # Process the document
            result = self.processor.process_document(
                file_path=file.name,
                extract_structure=extract_structure,
                extract_tables=extract_tables,
                ocr_images=ocr_images
            )
            
            progress(0.8, desc="Formatting results...")
            
            if result.get("success"):
                # Format output
                output_text = self._format_result(result)
                
                # Save result
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.output_dir / f"docling_result_{timestamp_str}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                progress(1.0, desc="Complete!")
                
                status = f"""✅ Processing complete!

**File:** {Path(file.name).name}
**Processing mode:** {result['metadata'].get('processing_mode', 'unknown')}
**Output saved to:** {output_file}
"""
                return status, output_text, str(output_file)
            else:
                return f"❌ Processing failed: {result.get('error', 'Unknown error')}", None, None
                
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return f"❌ Error: {str(e)}", None, None
    
    def batch_process_documents(
        self,
        extract_structure: bool,
        extract_tables: bool,
        ocr_images: bool,
        progress=gr.Progress()
    ) -> str:
        """Batch process documents from input directory"""
        if self.processor is None:
            return "❌ Please initialize the processor first!"
        
        try:
            progress(0.1, desc="Discovering files...")
            
            # Process batch
            results = self.processor.batch_process(
                input_dir=str(self.input_dir),
                output_dir=str(self.output_dir),
                extract_structure=extract_structure,
                extract_tables=extract_tables,
                ocr_images=ocr_images
            )
            
            progress(0.9, desc="Generating summary...")
            
            # Generate summary
            successful = sum(1 for r in results if r.get("success"))
            failed = len(results) - successful
            
            summary = f"""✅ Batch processing complete!

**Statistics:**
- Total files: {len(results)}
- Successful: {successful}
- Failed: {failed}

**Results saved to:** {self.output_dir}

**Processed files:**
"""
            for result in results:
                status = "✅" if result.get("success") else "❌"
                filename = Path(result['file_path']).name
                mode = result.get('metadata', {}).get('processing_mode', 'unknown')
                summary += f"\n{status} {filename} ({mode})"
            
            progress(1.0, desc="Complete!")
            return summary
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return f"❌ Error: {str(e)}"
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format processing result for display"""
        output = []
        
        # Add metadata
        output.append("=== PROCESSING METADATA ===\n")
        output.append(f"File: {Path(result['file_path']).name}")
        output.append(f"Timestamp: {result['timestamp']}")
        output.append(f"Mode: {result['metadata'].get('processing_mode', 'unknown')}")
        output.append("")
        
        # Add combined text
        if result.get('combined_text'):
            output.append("=== EXTRACTED CONTENT ===\n")
            output.append(result['combined_text'])
        
        return "\n".join(output)
    
    def get_capabilities_info(self) -> str:
        """Get processor capabilities information"""
        if self.processor is None:
            return "❌ Processor not initialized"
        
        try:
            capabilities = self.processor.get_capabilities()
            
            info = f"""**Processor Capabilities:**

**Docling Status:** {'✅ Enabled' if capabilities['docling_available'] else '❌ Disabled'}
**GutenOCR Model:** {capabilities['gutenocr_model']}

**Device Information:**
- Device: {capabilities['device_info']['device']}
- Using CPU: {capabilities['device_info']['use_cpu']}
- Data type: {capabilities['device_info']['torch_dtype']}
- CUDA available: {capabilities['device_info']['cuda_available']}
- CUDA devices: {capabilities['device_info']['cuda_device_count']}

**Supported Formats:**
{', '.join(capabilities['supported_formats'])}
"""
            return info
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        
        with gr.Blocks(
            title="Docling + GutenOCR Combined Processor"
        ) as interface:
            
            gr.Markdown("""
            # 📄 Docling + GutenOCR Combined Processor
            
            Advanced document processing combining Docling's structure extraction with GutenOCR's OCR capabilities.
            
            **Features:**
            - Document structure extraction (Docling)
            - Table detection and extraction
            - High-quality OCR (GutenOCR)
            - Support for PDF, DOCX, PPTX, images, and more
            """)
            
            # Setup Tab
            with gr.Tab("⚙️ Setup"):
                gr.Markdown("### Initialize Processor")
                
                with gr.Row():
                    model_choice = gr.Radio(
                        choices=["GutenOCR-3B", "GutenOCR-7B"],
                        value="GutenOCR-3B",
                        label="Model Selection",
                        info="3B is faster, 7B is more accurate"
                    )
                    use_cpu = gr.Checkbox(
                        label="Force CPU",
                        value=False,
                        info="Use CPU even if GPU is available"
                    )
                    use_docling = gr.Checkbox(
                        label="Enable Docling",
                        value=True,
                        info="Enable Docling for structure extraction"
                    )
                
                init_button = gr.Button("Initialize Processor", variant="primary")
                init_output = gr.Textbox(label="Status", lines=10)
                
                init_button.click(
                    fn=self.initialize_processor,
                    inputs=[model_choice, use_cpu, use_docling],
                    outputs=init_output
                )
                
                gr.Markdown("### Capabilities")
                capabilities_button = gr.Button("Show Capabilities")
                capabilities_output = gr.Markdown()
                
                capabilities_button.click(
                    fn=self.get_capabilities_info,
                    outputs=capabilities_output
                )
            
            # Single Document Tab
            with gr.Tab("📄 Single Document"):
                gr.Markdown("### Process Single Document")
                
                with gr.Row():
                    with gr.Column():
                        file_input = gr.File(
                            label="Upload Document",
                            file_types=[".pdf", ".docx", ".pptx", ".png", ".jpg", ".jpeg", ".tiff"]
                        )
                        
                        gr.Markdown("### Processing Options")
                        extract_structure = gr.Checkbox(
                            label="Extract Structure",
                            value=True,
                            info="Extract document structure with Docling"
                        )
                        extract_tables = gr.Checkbox(
                            label="Extract Tables",
                            value=True,
                            info="Detect and extract tables"
                        )
                        ocr_images = gr.Checkbox(
                            label="Perform OCR",
                            value=True,
                            info="Extract text with GutenOCR"
                        )
                        
                        process_button = gr.Button("Process Document", variant="primary")
                    
                    with gr.Column():
                        status_output = gr.Textbox(label="Status", lines=5)
                        result_output = gr.Textbox(
                            label="Extracted Content",
                            lines=20,
                            max_lines=30
                        )
                        output_file = gr.Textbox(label="Output File Path")
                
                process_button.click(
                    fn=self.process_single_document,
                    inputs=[file_input, extract_structure, extract_tables, ocr_images],
                    outputs=[status_output, result_output, output_file]
                )
            
            # Batch Processing Tab
            with gr.Tab("📚 Batch Processing"):
                gr.Markdown(f"""
                ### Batch Process Documents
                
                Process all documents in the input directory: `{self.input_dir}`
                
                **Instructions:**
                1. Place your documents in the `{self.input_dir}` directory
                2. Configure processing options below
                3. Click "Start Batch Processing"
                4. Results will be saved to `{self.output_dir}`
                """)
                
                with gr.Row():
                    batch_extract_structure = gr.Checkbox(
                        label="Extract Structure",
                        value=True
                    )
                    batch_extract_tables = gr.Checkbox(
                        label="Extract Tables",
                        value=True
                    )
                    batch_ocr_images = gr.Checkbox(
                        label="Perform OCR",
                        value=True
                    )
                
                batch_button = gr.Button("Start Batch Processing", variant="primary")
                batch_output = gr.Textbox(label="Results", lines=20)
                
                batch_button.click(
                    fn=self.batch_process_documents,
                    inputs=[batch_extract_structure, batch_extract_tables, batch_ocr_images],
                    outputs=batch_output
                )
            
            # Help Tab
            with gr.Tab("❓ Help"):
                gr.Markdown("""
                ## How to Use
                
                ### 1. Setup
                - Choose your model (3B for speed, 7B for accuracy)
                - Select CPU or GPU processing
                - Enable/disable Docling integration
                - Click "Initialize Processor"
                
                ### 2. Single Document Processing
                - Upload a document (PDF, DOCX, PPTX, or image)
                - Configure processing options:
                  - **Extract Structure**: Use Docling to extract document structure
                  - **Extract Tables**: Detect and extract tables from documents
                  - **Perform OCR**: Use GutenOCR for text extraction
                - Click "Process Document"
                - View results and download output file
                
                ### 3. Batch Processing
                - Place documents in the `./input` directory
                - Configure processing options
                - Click "Start Batch Processing"
                - Results saved to `./output` directory
                
                ## Supported Formats
                
                - **PDF**: Portable Document Format
                - **DOCX**: Microsoft Word documents
                - **PPTX**: Microsoft PowerPoint presentations
                - **Images**: PNG, JPG, JPEG, TIFF, BMP, GIF, WEBP
                - **HTML**: Web pages
                - **MD**: Markdown files
                
                ## Processing Modes
                
                - **Combined**: Uses both Docling and GutenOCR
                - **Docling Only**: Structure extraction without OCR
                - **GutenOCR Only**: OCR without structure extraction
                
                ## Tips
                
                - Use GPU for faster processing
                - GutenOCR-3B is recommended for most use cases
                - Enable all options for comprehensive document analysis
                - Check the output directory for detailed JSON results
                
                ## Troubleshooting
                
                - **Out of Memory**: Use GutenOCR-3B or enable CPU mode
                - **Docling Not Available**: Install with `pip install docling`
                - **Slow Processing**: Enable GPU if available
                """)
        
        return interface
    
    def launch(
        self,
        server_name: str = "0.0.0.0",
        server_port: int = 7861,
        share: bool = False
    ):
        """Launch the Gradio interface"""
        interface = self.create_interface()
        interface.launch(
            server_name=server_name,
            server_port=server_port,
            share=share
        )


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Docling + GutenOCR Combined UI")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=7861, help="Server port")
    parser.add_argument("--share", action="store_true", help="Create public link")
    
    args = parser.parse_args()
    
    ui = DoclingGutenOCRUI()
    ui.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share
    )


if __name__ == "__main__":
    main()

# Made with Bob