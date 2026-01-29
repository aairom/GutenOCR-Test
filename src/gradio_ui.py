# gradio_ui.py
"""
Gradio UI for GutenOCR Application
"""
import gradio as gr
import os
from pathlib import Path
from typing import List, Tuple
import logging
from gutenocr_engine import GutenOCREngine
from file_processor import FileProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GutenOCRUI:
    """
    Gradio-based UI for GutenOCR
    """
    
    def __init__(self):
        self.engine = None
        self.file_processor = FileProcessor()
        self.current_model = None
        self.use_cpu = False
    
    def initialize_engine(
        self,
        model_choice: str,
        use_cpu: bool
    ) -> str:
        """Initialize the OCR engine"""
        try:
            model_map = {
                "GutenOCR-3B (Faster)": "rootsautomation/GutenOCR-3B",
                "GutenOCR-7B (More Accurate)": "rootsautomation/GutenOCR-7B"
            }
            
            model_id = model_map.get(model_choice, "rootsautomation/GutenOCR-3B")
            
            logger.info(f"Initializing engine with model: {model_id}, CPU: {use_cpu}")
            self.engine = GutenOCREngine(
                model_id=model_id,
                use_cpu=use_cpu
            )
            self.current_model = model_choice
            self.use_cpu = use_cpu
            
            device_info = self.engine.get_device_info()
            return f"✓ Model loaded successfully!\n\nDevice Info:\n{self._format_device_info(device_info)}"
        
        except Exception as e:
            logger.error(f"Error initializing engine: {e}")
            return f"✗ Error loading model: {str(e)}"
    
    def _format_device_info(self, info: dict) -> str:
        """Format device information for display"""
        lines = []
        for key, value in info.items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines)
    
    def process_single_image(
        self,
        image_path: str,
        task_type: str,
        output_format: str
    ) -> Tuple[str, str]:
        """Process a single image"""
        if self.engine is None:
            return "Error: Please initialize the model first!", ""
        
        try:
            result = self.engine.process_image(
                image_path=image_path,
                task_type=task_type.lower().replace(" ", "_"),
                output_format=output_format
            )
            
            if result.get('success'):
                text_output = result.get('text', '')
                info = f"✓ Processing successful\n\nTask: {task_type}\nFormat: {output_format}\n\nCharacters: {len(text_output)}"
                return text_output, info
            else:
                error_msg = result.get('error', 'Unknown error')
                return f"Error: {error_msg}", "✗ Processing failed"
        
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return f"Error: {str(e)}", "✗ Processing failed"
    
    def process_batch(
        self,
        task_type: str,
        output_format: str,
        save_format: str,
        progress=gr.Progress()
    ) -> str:
        """Process all images in input directory"""
        if self.engine is None:
            return "Error: Please initialize the model first!"
        
        try:
            # Discover images
            progress(0, desc="Discovering images...")
            image_files = self.file_processor.discover_images(recursive=True)
            
            if not image_files:
                return "No images found in ./input directory"
            
            # Process images
            results = []
            for idx, image_path in enumerate(image_files):
                progress((idx + 1) / len(image_files), desc=f"Processing {idx + 1}/{len(image_files)}")
                
                result = self.engine.process_image(
                    image_path=image_path,
                    task_type=task_type.lower().replace(" ", "_"),
                    output_format=output_format
                )
                results.append(result)
            
            # Save results
            progress(0.9, desc="Saving results...")
            output_path = self.file_processor.save_results(
                results,
                format=save_format.lower(),
                timestamp=True
            )
            
            # Generate statistics
            stats = self.file_processor.get_statistics(results)
            summary_path = self.file_processor.create_summary_report(results, stats)
            
            # Save individual files
            individual_paths = self.file_processor.save_individual_results(results, format="txt")
            
            progress(1.0, desc="Complete!")
            
            return f"""✓ Batch processing complete!

Processed: {stats['total_images']} images
Success: {stats['successful']} ({stats['success_rate']})
Failed: {stats['failed']}

Output files:
- Combined results: {output_path}
- Summary report: {summary_path}
- Individual files: {len(individual_paths)} files saved

Total characters extracted: {stats['total_characters']}
Average per image: {stats['average_characters_per_image']}
"""
        
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            return f"Error: {str(e)}"
    
    def create_interface(self) -> gr.Blocks:
        """Create the Gradio interface"""
        
        with gr.Blocks(title="GutenOCR Application", theme=gr.themes.Soft()) as interface:
            gr.Markdown("""
            # 🔍 GutenOCR Application
            
            Advanced OCR powered by Vision Language Models with CPU/GPU support
            """)
            
            with gr.Tab("⚙️ Setup"):
                gr.Markdown("### Model Configuration")
                
                with gr.Row():
                    model_choice = gr.Radio(
                        choices=["GutenOCR-3B (Faster)", "GutenOCR-7B (More Accurate)"],
                        value="GutenOCR-3B (Faster)",
                        label="Select Model"
                    )
                    use_cpu = gr.Checkbox(
                        label="Force CPU Usage (slower but works without GPU)",
                        value=False
                    )
                
                init_btn = gr.Button("Initialize Model", variant="primary", size="lg")
                init_output = gr.Textbox(label="Initialization Status", lines=8)
                
                init_btn.click(
                    fn=self.initialize_engine,
                    inputs=[model_choice, use_cpu],
                    outputs=init_output
                )
            
            with gr.Tab("📄 Single Image"):
                gr.Markdown("### Process a Single Image")
                
                with gr.Row():
                    with gr.Column():
                        single_image = gr.Image(type="filepath", label="Upload Image")
                        
                        single_task = gr.Dropdown(
                            choices=["Reading", "Detection", "Localized Reading", "Conditional Detection"],
                            value="Reading",
                            label="Task Type"
                        )
                        
                        single_format = gr.Dropdown(
                            choices=["TEXT", "TEXT2D", "LINES", "WORDS", "PARAGRAPHS", "LATEX", "BOX"],
                            value="TEXT",
                            label="Output Format"
                        )
                        
                        single_process_btn = gr.Button("Process Image", variant="primary")
                    
                    with gr.Column():
                        single_output = gr.Textbox(label="OCR Result", lines=15)
                        single_info = gr.Textbox(label="Processing Info", lines=5)
                
                single_process_btn.click(
                    fn=self.process_single_image,
                    inputs=[single_image, single_task, single_format],
                    outputs=[single_output, single_info]
                )
            
            with gr.Tab("📁 Batch Processing"):
                gr.Markdown("""
                ### Batch Process Images
                
                Process all images in the `./input` directory recursively.
                Results will be saved to `./output` directory with timestamps.
                """)
                
                with gr.Row():
                    batch_task = gr.Dropdown(
                        choices=["Reading", "Detection", "Localized Reading", "Conditional Detection"],
                        value="Reading",
                        label="Task Type"
                    )
                    
                    batch_format = gr.Dropdown(
                        choices=["TEXT", "TEXT2D", "LINES", "WORDS", "PARAGRAPHS", "LATEX", "BOX"],
                        value="TEXT",
                        label="Output Format"
                    )
                    
                    save_format = gr.Dropdown(
                        choices=["JSON", "TXT", "CSV"],
                        value="JSON",
                        label="Save Format"
                    )
                
                batch_process_btn = gr.Button("Start Batch Processing", variant="primary", size="lg")
                batch_output = gr.Textbox(label="Batch Processing Results", lines=15)
                
                batch_process_btn.click(
                    fn=self.process_batch,
                    inputs=[batch_task, batch_format, save_format],
                    outputs=batch_output
                )
            
            with gr.Tab("ℹ️ Info"):
                gr.Markdown("""
                ## About GutenOCR
                
                GutenOCR is a state-of-the-art OCR system powered by Vision Language Models.
                
                ### Features:
                - **Multiple Models**: Choose between 3B (faster) and 7B (more accurate) models
                - **CPU/GPU Support**: Works on both CPU and GPU (GPU recommended for speed)
                - **Flexible Tasks**: Reading, detection, localized reading, conditional detection
                - **Multiple Formats**: TEXT, TEXT2D, LINES, WORDS, PARAGRAPHS, LATEX, BOX
                - **Batch Processing**: Process entire directories recursively
                - **Timestamped Output**: All results saved with timestamps
                
                ### Task Types:
                - **Reading**: Extract all text from the image
                - **Detection**: Locate text regions without transcription
                - **Localized Reading**: Read text in specific regions
                - **Conditional Detection**: Find specific text queries
                
                ### Output Formats:
                - **TEXT**: Plain text, linearized
                - **TEXT2D**: Layout-preserving text
                - **LINES**: Line-by-line with bounding boxes
                - **WORDS**: Word-by-word with bounding boxes
                - **PARAGRAPHS**: Paragraph-wise with bounding boxes
                - **LATEX**: LaTeX expressions with bounding boxes
                - **BOX**: Bounding boxes only (for detection)
                
                ### Directory Structure:
                - `./input`: Place your images here (supports recursive subdirectories)
                - `./output`: Results are saved here with timestamps
                
                ### Supported Formats:
                PNG, JPG, JPEG, TIFF, TIF, BMP, GIF, WEBP, PDF
                """)
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        interface = self.create_interface()
        interface.launch(**kwargs)


def main():
    """Main entry point"""
    app = GutenOCRUI()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()

# Made with Bob
