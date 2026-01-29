# GutenOCR Application

A comprehensive OCR application powered by GutenOCR Vision Language Models with CPU/GPU support, featuring a user-friendly interface and combined Docling integration.

![GutenOCR](https://img.shields.io/badge/GutenOCR-3B%20%7C%207B-blue)
![Python](https://img.shields.io/badge/Python-3.10+-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue)

## 🌟 Features

- **Multiple Models**: Support for GutenOCR-3B (faster) and GutenOCR-7B (more accurate)
- **CPU/GPU Support**: Works on both CPU and GPU (GPU recommended for speed)
- **User-Friendly UI**: Gradio-based web interface for easy interaction
- **Batch Processing**: Process entire directories recursively
- **Combined Processing**: Integration with Docling for enhanced document processing
- **Flexible Tasks**: Reading, detection, localized reading, conditional detection
- **Multiple Output Formats**: TEXT, TEXT2D, LINES, WORDS, PARAGRAPHS, LATEX, BOX
- **Timestamped Output**: All results saved with timestamps
- **Docker Support**: Ready-to-use Docker containers for CPU and GPU
- **Kubernetes Ready**: Complete K8s deployment configurations
- **Automation Scripts**: Automated start, stop, and GitHub push scripts

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Architecture](#architecture)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- (Optional) CUDA-capable GPU for faster processing
- (Optional) Docker for containerized deployment
- (Optional) Kubernetes cluster for production deployment

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/GutenOCR-Test.git
cd GutenOCR-Test
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🎯 Quick Start

### Option 1: Gradio UI (Recommended)

Start the web interface:
```bash
./scripts/start.sh --mode gradio
```

Access the UI at: `http://localhost:7860`

### Option 2: Command Line (Combined Processor)

Process images directly:
```bash
./scripts/start.sh --mode combined
```

### Option 3: Docker

Start with Docker (CPU):
```bash
./scripts/start.sh --mode docker-cpu
```

Start with Docker (GPU):
```bash
./scripts/start.sh --mode docker-gpu
```

## 📖 Usage

### Gradio Web Interface

1. **Setup Tab**: Initialize the model
   - Select model (3B or 7B)
   - Choose CPU or GPU
   - Click "Initialize Model"

2. **Single Image Tab**: Process individual images
   - Upload an image
   - Select task type and output format
   - Click "Process Image"

3. **Batch Processing Tab**: Process multiple images
   - Place images in `./input` directory
   - Select processing options
   - Click "Start Batch Processing"
   - Results saved to `./output` directory

### Command Line Interface

#### Process Single Image
```python
from src.gutenocr_engine import GutenOCREngine

engine = GutenOCREngine(
    model_id="rootsautomation/GutenOCR-3B",
    use_cpu=False  # Set to True for CPU
)

result = engine.process_image(
    image_path="path/to/image.png",
    task_type="reading",
    output_format="TEXT"
)

print(result['text'])
```

#### Batch Processing
```python
from src.gutenocr_engine import GutenOCREngine
from src.file_processor import FileProcessor

engine = GutenOCREngine()
processor = FileProcessor()

# Discover images
images = processor.discover_images(recursive=True)

# Process batch
results = engine.batch_process(images)

# Save results
processor.save_results(results, format="json")
```

#### Combined Docling + GutenOCR
```bash
python src/docling_gutenocr_combined.py \
    --input ./input \
    --output ./output \
    --model rootsautomation/GutenOCR-3B
```

## 🏗️ Architecture

### Project Structure

```
GutenOCR-Test/
├── src/
│   ├── gutenocr_engine.py          # Core OCR engine
│   ├── file_processor.py           # File handling and output management
│   ├── gradio_ui.py                # Web interface
│   └── docling_gutenocr_combined.py # Combined processor
├── docker/
│   ├── Dockerfile.gutenocr         # CPU Docker image
│   ├── Dockerfile.gutenocr-gpu     # GPU Docker image
│   ├── Dockerfile.combined         # Combined processor image
│   ├── docker-compose.yml          # Docker Compose configuration
│   └── .dockerignore               # Docker ignore file
├── kubernetes/
│   ├── deployment-cpu.yaml         # CPU deployment
│   ├── deployment-gpu.yaml         # GPU deployment
│   ├── persistent-volumes.yaml     # Storage configuration
│   ├── configmap.yaml              # Configuration
│   └── ingress.yaml                # Ingress rules
├── scripts/
│   ├── start.sh                    # Start script
│   ├── stop.sh                     # Stop script
│   └── push-to-github.sh           # GitHub automation
├── input/                          # Input images directory
├── output/                         # Output results directory
├── docs/                           # Documentation
├── tests/                          # Test files
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

### Component Overview

See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed information.

## 🐳 Docker Deployment

### Build Images

```bash
# CPU version
docker build -f docker/Dockerfile.gutenocr -t gutenocr:cpu-latest .

# GPU version
docker build -f docker/Dockerfile.gutenocr-gpu -t gutenocr:gpu-latest .

# Combined processor
docker build -f docker/Dockerfile.combined -t gutenocr:combined-latest .
```

### Run Containers

```bash
# CPU version
docker run -d \
    --name gutenocr-cpu \
    -p 7860:7860 \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    gutenocr:cpu-latest

# GPU version (requires nvidia-docker)
docker run -d \
    --name gutenocr-gpu \
    --gpus all \
    -p 7860:7860 \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    gutenocr:gpu-latest
```

### Docker Compose

```bash
# Start CPU version
docker-compose -f docker/docker-compose.yml up -d gutenocr-cpu

# Start GPU version
docker-compose -f docker/docker-compose.yml up -d gutenocr-gpu

# Start combined processor
docker-compose -f docker/docker-compose.yml --profile batch up combined-processor
```

## ☸️ Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- (Optional) NVIDIA GPU Operator for GPU support

### Deploy to Kubernetes

```bash
# Deploy using automation script
./scripts/start.sh --mode k8s

# Or manually:
kubectl apply -f kubernetes/persistent-volumes.yaml
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/deployment-cpu.yaml
kubectl apply -f kubernetes/deployment-gpu.yaml
kubectl apply -f kubernetes/ingress.yaml
```

### Check Deployment Status

```bash
# Check pods
kubectl get pods -l app=gutenocr

# Check services
kubectl get services -l app=gutenocr

# View logs
kubectl logs -f deployment/gutenocr-cpu
```

### Scale Deployment

```bash
# Scale CPU deployment
kubectl scale deployment gutenocr-cpu --replicas=3

# Scale GPU deployment
kubectl scale deployment gutenocr-gpu --replicas=2
```

## 📚 API Reference

### GutenOCREngine

```python
class GutenOCREngine:
    def __init__(
        self,
        model_id: str = "rootsautomation/GutenOCR-3B",
        device: str = "auto",
        use_cpu: bool = False,
        torch_dtype: Optional[torch.dtype] = None
    )
    
    def process_image(
        self,
        image_path: str,
        task_type: str = "reading",
        output_format: str = "TEXT",
        max_new_tokens: int = 4096,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]
    
    def batch_process(
        self,
        image_paths: List[str],
        task_type: str = "reading",
        output_format: str = "TEXT",
        max_new_tokens: int = 4096
    ) -> List[Dict[str, Any]]
```

### Task Types

- **reading**: Extract all text from the image
- **detection**: Locate text regions without transcription
- **localized_reading**: Read text in specific regions
- **conditional_detection**: Find specific text queries

### Output Formats

- **TEXT**: Plain text, linearized
- **TEXT2D**: Layout-preserving text
- **LINES**: Line-by-line with bounding boxes
- **WORDS**: Word-by-word with bounding boxes
- **PARAGRAPHS**: Paragraph-wise with bounding boxes
- **LATEX**: LaTeX expressions with bounding boxes
- **BOX**: Bounding boxes only (for detection)

## ⚙️ Configuration

### Environment Variables

```bash
# Model configuration
GUTENOCR_MODEL=rootsautomation/GutenOCR-3B
GUTENOCR_USE_CPU=false

# Server configuration
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860

# Processing configuration
MAX_NEW_TOKENS=4096
DEFAULT_TASK_TYPE=reading
DEFAULT_OUTPUT_FORMAT=TEXT
```

### Model Selection

- **GutenOCR-3B**: Faster, lower memory requirements (~6GB VRAM)
- **GutenOCR-7B**: More accurate, higher memory requirements (~14GB VRAM)

### CPU vs GPU

**GPU (Recommended)**:
- Faster processing (10-50x speedup)
- Requires CUDA-capable GPU
- Higher memory requirements

**CPU**:
- Slower processing
- Works on any machine
- Lower memory requirements
- Set `use_cpu=True` in engine initialization

## 🔧 Troubleshooting

### Common Issues

#### Out of Memory Error
```
Solution: Use GutenOCR-3B instead of 7B, or enable CPU mode
```

#### CUDA Not Available
```
Solution: Install CUDA toolkit or use CPU mode with --cpu flag
```

#### Model Download Fails
```
Solution: Check internet connection and HuggingFace access
Set HF_TOKEN environment variable if needed
```

#### Port Already in Use
```
Solution: Change port in environment variables or stop conflicting service
```

### Performance Optimization

1. **Use GPU**: Significantly faster than CPU
2. **Batch Processing**: More efficient for multiple images
3. **Model Selection**: Use 3B for speed, 7B for accuracy
4. **Image Size**: Resize large images before processing

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

The GutenOCR model weights are licensed under CC-BY-NC.

## 🙏 Acknowledgments

- [GutenOCR](https://github.com/Roots-Automation/GutenOCR) - Original OCR models
- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL) - Base vision-language model
- [Docling](https://github.com/docling-project/docling) - Document processing
- [Gradio](https://gradio.app/) - Web interface framework

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/YOUR_USERNAME/GutenOCR-Test/issues)
- Discussions: [GitHub Discussions](https://github.com/YOUR_USERNAME/GutenOCR-Test/discussions)

## 🗺️ Roadmap

- [ ] Add support for more languages
- [ ] Implement real-time OCR streaming
- [ ] Add REST API endpoint
- [ ] Improve batch processing performance
- [ ] Add more output formats
- [ ] Implement caching mechanism
- [ ] Add monitoring and metrics

---

**Built with ❤️ using GutenOCR**