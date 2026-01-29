# GutenOCR Application Architecture

## Overview

This document describes the architecture of the GutenOCR application, including its components, data flow, and deployment options.

## System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI1[Standard Gradio UI<br/>Port 7860]
        UI2[Docling + GutenOCR UI<br/>Port 7861]
        CLI[Command Line Interface]
    end
    
    subgraph "Application Layer"
        Engine[GutenOCR Engine]
        FileProc[File Processor]
        Combined[Docling+GutenOCR Combined]
    end
    
    subgraph "Model Layer"
        Model3B[GutenOCR-3B Model]
        Model7B[GutenOCR-7B Model]
        Docling[Docling Processor]
    end
    
    subgraph "Storage Layer"
        Input[Input Directory]
        Output[Output Directory]
        Cache[Model Cache]
    end
    
    subgraph "Infrastructure Layer"
        Docker[Docker Containers]
        K8s[Kubernetes Cluster]
    end
    
    UI1 --> Engine
    UI2 --> Combined
    CLI --> Engine
    CLI --> Combined
    
    Engine --> Model3B
    Engine --> Model7B
    Engine --> FileProc
    
    Combined --> Engine
    Combined --> Docling
    Combined --> FileProc
    
    FileProc --> Input
    FileProc --> Output
    
    Model3B --> Cache
    Model7B --> Cache
    
    Engine -.-> Docker
    Combined -.-> Docker
    Docker -.-> K8s
```

## Component Details

### 1. GutenOCR Engine (`gutenocr_engine.py`)

**Purpose**: Core OCR processing engine

**Key Features**:
- Model loading and initialization
- CPU/GPU device management
- Image processing with multiple task types
- Batch processing capabilities
- Flexible output formats

**Key Methods**:
```python
- __init__(model_id, device, use_cpu, torch_dtype)
- process_image(image_path, task_type, output_format, max_new_tokens)
- batch_process(image_paths, task_type, output_format)
- get_device_info()
```

**Supported Models**:
- GutenOCR-3B: 3 billion parameters, faster processing
- GutenOCR-7B: 7 billion parameters, higher accuracy

**Task Types**:
- Reading: Full text extraction
- Detection: Text region localization
- Localized Reading: Region-specific text extraction
- Conditional Detection: Query-based text finding

### 2. File Processor (`file_processor.py`)

**Purpose**: File discovery and output management

**Key Features**:
- Recursive file discovery
- Multiple output formats (JSON, TXT, CSV)
- Timestamped output files
- Statistics generation
- Summary report creation

**Key Methods**:
```python
- discover_images(recursive)
- save_results(results, format, timestamp)
- save_individual_results(results, format)
- get_statistics(results)
- create_summary_report(results, statistics)
```

### 3. Standard Gradio UI (`gradio_ui.py`)

**Purpose**: Web-based user interface for standard OCR tasks

**Port**: 7860

**Key Features**:
- Model initialization interface
- Single image processing
- Batch processing
- Real-time progress tracking
- Device information display

**Tabs**:
1. Setup: Model configuration and initialization
2. Single Image: Individual image processing
3. Batch Processing: Directory-based processing
4. Info: Documentation and help

### 3.5. Docling + GutenOCR UI (`docling_gradio_ui.py`) **NEW!**

**Purpose**: Advanced document processing interface combining Docling and GutenOCR

**Port**: 7861

**Key Features**:
- Combined processor initialization
- Document structure extraction
- Table detection and extraction
- Multi-format support (PDF, DOCX, PPTX, images)
- Processing mode selection
- Comprehensive help system

**Tabs**:
1. Setup: Processor configuration and capabilities
2. Single Document: Individual document processing with options
3. Batch Processing: Directory-based document processing
4. Help: Comprehensive usage guide and troubleshooting

**Processing Options**:
- Extract Structure: Use Docling for document structure
- Extract Tables: Detect and extract tables
- Perform OCR: Use GutenOCR for text extraction

**Processing Modes**:
- Combined: Both Docling and GutenOCR
- Docling Only: Structure extraction without OCR
- GutenOCR Only: OCR without structure extraction

### 4. Combined Processor (`docling_gutenocr_combined.py`)

**Purpose**: Backend integration of Docling and GutenOCR

**Key Features**:
- Document structure extraction (Docling)
- OCR processing (GutenOCR)
- Table extraction
- Result merging
- Batch processing
- Multi-format support

**Supported Formats**:
- PDF, DOCX, PPTX (with Docling)
- PNG, JPG, JPEG, TIFF, BMP, GIF, WEBP (images)
- HTML, Markdown (with Docling)

**Processing Pipeline**:
1. Extract document structure with Docling (optional)
2. Perform OCR with GutenOCR (optional)
3. Merge results intelligently
4. Save combined output with metadata

**Key Methods**:
```python
- __init__(gutenocr_model, use_cpu, use_docling)
- process_document(file_path, extract_structure, extract_tables, ocr_images)
- batch_process(input_dir, output_dir, extract_structure, extract_tables, ocr_images)
- get_capabilities()
```

## Data Flow

### Single Image Processing (Standard UI)

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant Engine
    participant Model
    participant Storage
    
    User->>UI: Upload Image
    User->>UI: Select Options
    UI->>Engine: process_image()
    Engine->>Model: Load & Process
    Model->>Engine: OCR Results
    Engine->>UI: Return Results
    UI->>User: Display Results
    
    opt Save Results
        UI->>Storage: Save to Output
    end
```

### Single Document Processing (Docling UI)

```mermaid
sequenceDiagram
    participant User
    participant DoclingUI
    participant Combined
    participant Docling
    participant GutenOCR
    participant Storage
    
    User->>DoclingUI: Upload Document
    User->>DoclingUI: Select Processing Options
    DoclingUI->>Combined: process_document()
    
    alt Extract Structure
        Combined->>Docling: Extract Structure
        Docling->>Combined: Structure Data
    end
    
    alt Perform OCR
        Combined->>GutenOCR: Process Image
        GutenOCR->>Combined: OCR Results
    end
    
    Combined->>Combined: Merge Results
    Combined->>Storage: Save Combined Output
    Combined->>DoclingUI: Return Results
    DoclingUI->>User: Display Content
```

### Batch Processing

```mermaid
sequenceDiagram
    participant User
    participant FileProc
    participant Engine
    participant Model
    participant Storage
    
    User->>FileProc: Start Batch
    FileProc->>Storage: Discover Images
    Storage->>FileProc: Image List
    
    loop For Each Image
        FileProc->>Engine: process_image()
        Engine->>Model: Process
        Model->>Engine: Results
        Engine->>FileProc: Results
    end
    
    FileProc->>Storage: Save All Results
    FileProc->>Storage: Save Statistics
    FileProc->>User: Complete
```

## Deployment Architecture

### Docker Deployment

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "CPU Container"
            AppCPU[GutenOCR App]
            ModelCPU[Model Cache]
        end
        
        subgraph "GPU Container"
            AppGPU[GutenOCR App]
            ModelGPU[Model Cache]
            GPU[NVIDIA GPU]
        end
        
        subgraph "Volumes"
            Input[Input Volume]
            Output[Output Volume]
            Cache[Model Cache Volume]
        end
    end
    
    AppCPU --> Input
    AppCPU --> Output
    AppCPU --> Cache
    
    AppGPU --> Input
    AppGPU --> Output
    AppGPU --> Cache
    AppGPU --> GPU
    
    User[Users] --> AppCPU
    User --> AppGPU
```

### Kubernetes Deployment

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Ingress Layer"
            Ingress[Nginx Ingress]
        end
        
        subgraph "Service Layer"
            SvcCPU[CPU Service]
            SvcGPU[GPU Service]
        end
        
        subgraph "Pod Layer"
            PodCPU1[CPU Pod 1]
            PodCPU2[CPU Pod 2]
            PodGPU1[GPU Pod 1]
        end
        
        subgraph "Storage Layer"
            PVC1[Input PVC]
            PVC2[Output PVC]
            PVC3[Cache PVC]
        end
        
        subgraph "Config Layer"
            CM[ConfigMap]
        end
    end
    
    Internet[Internet] --> Ingress
    Ingress --> SvcCPU
    Ingress --> SvcGPU
    
    SvcCPU --> PodCPU1
    SvcCPU --> PodCPU2
    SvcGPU --> PodGPU1
    
    PodCPU1 --> PVC1
    PodCPU1 --> PVC2
    PodCPU1 --> PVC3
    PodCPU1 --> CM
    
    PodCPU2 --> PVC1
    PodCPU2 --> PVC2
    PodCPU2 --> PVC3
    PodCPU2 --> CM
    
    PodGPU1 --> PVC1
    PodGPU1 --> PVC2
    PodGPU1 --> PVC3
    PodGPU1 --> CM
```

## Resource Requirements

### CPU Deployment

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| GutenOCR-3B | 2-4 cores | 4-8 GB | 10 GB |
| GutenOCR-7B | 4-8 cores | 8-16 GB | 20 GB |

### GPU Deployment

| Component | GPU | VRAM | Memory | Storage |
|-----------|-----|------|--------|---------|
| GutenOCR-3B | 1x GPU | 6 GB | 8 GB | 10 GB |
| GutenOCR-7B | 1x GPU | 14 GB | 16 GB | 20 GB |

## Performance Characteristics

### Processing Speed

| Model | Device | Images/Hour | Avg Time/Image |
|-------|--------|-------------|----------------|
| 3B | CPU | 10-20 | 3-6 min |
| 3B | GPU | 200-500 | 7-18 sec |
| 7B | CPU | 5-10 | 6-12 min |
| 7B | GPU | 100-300 | 12-36 sec |

*Note: Performance varies based on image size and complexity*

## Security Considerations

1. **Model Access**: Models downloaded from HuggingFace
2. **Data Privacy**: All processing done locally
3. **Network Security**: Use HTTPS in production
4. **Access Control**: Implement authentication for production
5. **Resource Limits**: Set appropriate resource quotas

## Scalability

### Horizontal Scaling

- **CPU Pods**: Can scale to multiple replicas
- **GPU Pods**: Limited by available GPUs
- **Load Balancing**: Handled by Kubernetes Service

### Vertical Scaling

- Increase CPU/Memory allocation
- Use larger GPU models
- Optimize batch sizes

## Monitoring and Logging

### Metrics to Monitor

- Request rate
- Processing time
- Error rate
- Resource utilization (CPU, Memory, GPU)
- Queue depth

### Logging

- Application logs: stdout/stderr
- Access logs: Ingress controller
- Error logs: Application and system level

## Future Enhancements

1. **Caching Layer**: Redis for result caching
2. **Queue System**: RabbitMQ/Kafka for async processing
3. **API Gateway**: REST API with authentication
4. **Monitoring**: Prometheus + Grafana
5. **Auto-scaling**: HPA based on metrics
6. **Multi-region**: Geographic distribution

## References

- [GutenOCR GitHub](https://github.com/Roots-Automation/GutenOCR)
- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL)
- [Docling](https://github.com/docling-project/docling)
- [Gradio Documentation](https://gradio.app/docs/)