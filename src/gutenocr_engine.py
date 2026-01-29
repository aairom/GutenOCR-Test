# gutenocr_engine.py
"""
GutenOCR Engine - Core OCR processing with CPU/GPU support
"""
import os
import torch
from typing import Optional, Dict, Any, List
from PIL import Image
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GutenOCREngine:
    """
    GutenOCR Engine for OCR processing with CPU/GPU support
    """
    
    def __init__(
        self,
        model_id: str = "rootsautomation/GutenOCR-3B",
        device: str = "auto",
        use_cpu: bool = False,
        torch_dtype: Optional[torch.dtype] = None
    ):
        """
        Initialize GutenOCR Engine
        
        Args:
            model_id: HuggingFace model ID (GutenOCR-3B or GutenOCR-7B)
            device: Device to use ('auto', 'cuda', 'cpu')
            use_cpu: Force CPU usage even if GPU is available
            torch_dtype: Torch data type (default: bfloat16 for GPU, float32 for CPU)
        """
        self.model_id = model_id
        self.use_cpu = use_cpu
        
        # Determine device and dtype
        if use_cpu or not torch.cuda.is_available():
            self.device = "cpu"
            self.torch_dtype = torch_dtype or torch.float32
            logger.info("Using CPU for inference")
        else:
            self.device = device
            self.torch_dtype = torch_dtype or torch.bfloat16
            logger.info(f"Using GPU for inference with dtype {self.torch_dtype}")
        
        # Load model and processor
        logger.info(f"Loading model: {model_id}")
        self.model = self._load_model()
        self.processor = AutoProcessor.from_pretrained(model_id)
        logger.info("Model loaded successfully")
    
    def _load_model(self) -> Qwen2_5_VLForConditionalGeneration:
        """Load the model with appropriate settings"""
        try:
            if self.use_cpu:
                # CPU-specific loading
                model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype,
                    device_map="cpu",
                    low_cpu_mem_usage=True
                )
            else:
                # GPU loading
                model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype,
                    device_map=self.device
                )
            return model
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def process_image(
        self,
        image_path: str,
        task_type: str = "reading",
        output_format: str = "TEXT",
        max_new_tokens: int = 4096,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process an image with OCR
        
        Args:
            image_path: Path to the image file
            task_type: Type of task ('reading', 'detection', 'localized_reading', 'conditional_detection')
            output_format: Output format ('TEXT', 'TEXT2D', 'LINES', 'WORDS', 'PARAGRAPHS', 'LATEX', 'BOX')
            max_new_tokens: Maximum number of tokens to generate
            custom_prompt: Custom prompt (overrides default)
        
        Returns:
            Dictionary with OCR results
        """
        try:
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Generate prompt
            if custom_prompt:
                prompt = custom_prompt
            else:
                prompt = self._generate_prompt(task_type, output_format)
            
            # Prepare messages
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt},
                    ],
                }
            ]
            
            # Process and generate
            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            
            # Move to device
            if self.use_cpu:
                inputs = {k: v.to("cpu") for k, v in inputs.items()}
            else:
                inputs = inputs.to(self.device)
            
            # Generate
            logger.info(f"Processing image: {image_path}")
            with torch.no_grad():
                generated_ids = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens
                )
            
            # Decode output
            generated_ids_trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            output_text = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )
            
            return {
                "success": True,
                "image_path": image_path,
                "task_type": task_type,
                "output_format": output_format,
                "text": output_text[0],
                "prompt": prompt
            }
            
        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            return {
                "success": False,
                "image_path": image_path,
                "error": str(e)
            }
    
    def _generate_prompt(self, task_type: str, output_format: str) -> str:
        """Generate appropriate prompt based on task type and output format"""
        prompts = {
            "reading": {
                "TEXT": "Read all text in the image and return a single TEXT string, linearized left-to-right/top-to-bottom.",
                "TEXT2D": "Return a layout-sensitive TEXT2D representation of the image.",
                "LINES": "Return line-by-line OCR as LINES with bounding boxes.",
                "WORDS": "Return word-by-word OCR as WORDS with bounding boxes.",
                "PARAGRAPHS": "Return paragraph-wise OCR as PARAGRAPHS with bounding boxes.",
                "LATEX": "Extract all LaTeX expressions with bounding boxes."
            },
            "detection": {
                "BOX": "Highlight all text regions in the image by returning their bounding boxes as a JSON array."
            },
            "localized_reading": {
                "TEXT": "What does it say in the specified region of the image?"
            },
            "conditional_detection": {
                "BOX": "Find and return bounding boxes for the specified text query."
            }
        }
        
        return prompts.get(task_type, {}).get(
            output_format,
            "Read all text in the image."
        )
    
    def batch_process(
        self,
        image_paths: List[str],
        task_type: str = "reading",
        output_format: str = "TEXT",
        max_new_tokens: int = 4096
    ) -> List[Dict[str, Any]]:
        """
        Process multiple images in batch
        
        Args:
            image_paths: List of image paths
            task_type: Type of task
            output_format: Output format
            max_new_tokens: Maximum tokens to generate
        
        Returns:
            List of results for each image
        """
        results = []
        for image_path in image_paths:
            result = self.process_image(
                image_path,
                task_type=task_type,
                output_format=output_format,
                max_new_tokens=max_new_tokens
            )
            results.append(result)
        return results
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get information about the device being used"""
        return {
            "device": self.device,
            "use_cpu": self.use_cpu,
            "torch_dtype": str(self.torch_dtype),
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "model_id": self.model_id
        }

# Made with Bob
