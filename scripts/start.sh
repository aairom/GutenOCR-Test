#!/bin/bash

# GutenOCR Start Script
# This script starts the GutenOCR application

set -e

echo "=========================================="
echo "GutenOCR Application Startup"
echo "=========================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored messages
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running in project directory
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found. Please run this script from the project root directory."
    exit 1
fi

# Parse command line arguments
MODE="gradio"
USE_CPU=false
MODEL="3B"

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --cpu)
            USE_CPU=true
            shift
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./scripts/start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE       Application mode: gradio, docling-ui, combined, docker-cpu, docker-gpu, k8s"
            echo "  --cpu             Force CPU usage (for gradio and combined modes)"
            echo "  --model MODEL     Model size: 3B or 7B (default: 3B)"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Create necessary directories
print_info "Creating directories..."
mkdir -p input output logs

# Generate timestamp for log files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

case $MODE in
    gradio)
        print_info "Starting GutenOCR Gradio UI..."
        
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            print_warning "Virtual environment not found. Creating one..."
            python3 -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Install dependencies
        print_info "Installing dependencies..."
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
        
        # Set model
        if [ "$MODEL" = "7B" ]; then
            export GUTENOCR_MODEL="rootsautomation/GutenOCR-7B"
        else
            export GUTENOCR_MODEL="rootsautomation/GutenOCR-3B"
        fi
        
        # Set CPU flag
        if [ "$USE_CPU" = true ]; then
            export GUTENOCR_USE_CPU="true"
            print_info "Running on CPU"
        else
            print_info "Running on GPU (if available)"
        fi
        
        # Create log file
        LOG_FILE="./output/gradio_ui_${TIMESTAMP}.log"
        PID_FILE="./output/gradio_ui.pid"
        
        print_info "Starting Gradio UI on http://localhost:7860"
        print_info "Logs: $LOG_FILE"
        
        # Start in background and save PID
        nohup python src/gradio_ui.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        
        print_info "Process started with PID: $(cat $PID_FILE)"
        print_info "Waiting for startup..."
        sleep 3
        
        # Tail the log file
        print_info "Tailing logs (Ctrl+C to stop viewing, app continues running)..."
        tail -f "$LOG_FILE"
        ;;
    
    docling-ui)
        print_info "Starting Docling + GutenOCR Combined UI..."
        
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            print_warning "Virtual environment not found. Creating one..."
            python3 -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Install dependencies
        print_info "Installing dependencies..."
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
        
        # Set model
        if [ "$MODEL" = "7B" ]; then
            export GUTENOCR_MODEL="rootsautomation/GutenOCR-7B"
        else
            export GUTENOCR_MODEL="rootsautomation/GutenOCR-3B"
        fi
        
        # Set CPU flag
        if [ "$USE_CPU" = true ]; then
            export GUTENOCR_USE_CPU="true"
            print_info "Running on CPU"
        else
            print_info "Running on GPU (if available)"
        fi
        
        # Create log file
        LOG_FILE="./output/docling_ui_${TIMESTAMP}.log"
        PID_FILE="./output/docling_ui.pid"
        
        print_info "Starting Docling + GutenOCR UI on http://localhost:7861"
        print_info "Logs: $LOG_FILE"
        
        # Start in background and save PID
        nohup python src/docling_gradio_ui.py > "$LOG_FILE" 2>&1 &
        echo $! > "$PID_FILE"
        
        print_info "Process started with PID: $(cat $PID_FILE)"
        print_info "Waiting for startup..."
        sleep 3
        
        # Tail the log file
        print_info "Tailing logs (Ctrl+C to stop viewing, app continues running)..."
        tail -f "$LOG_FILE"
        ;;
    
    combined)
        print_info "Starting Combined Docling + GutenOCR processor..."
        
        # Check if virtual environment exists
        if [ ! -d "venv" ]; then
            print_warning "Virtual environment not found. Creating one..."
            python3 -m venv venv
        fi
        
        # Activate virtual environment
        source venv/bin/activate
        
        # Install dependencies
        print_info "Installing dependencies..."
        pip install -q --upgrade pip
        pip install -q -r requirements.txt
        
        # Run combined processor
        CPU_FLAG=""
        if [ "$USE_CPU" = true ]; then
            CPU_FLAG="--cpu"
        fi
        
        MODEL_FLAG="--model rootsautomation/GutenOCR-${MODEL}"
        
        print_info "Processing files from ./input to ./output"
        python src/docling_gutenocr_combined.py --input ./input --output ./output $CPU_FLAG $MODEL_FLAG
        ;;
    
    docker-cpu)
        print_info "Starting GutenOCR with Docker (CPU)..."
        
        # Build image if it doesn't exist
        if ! docker images | grep -q "gutenocr.*cpu"; then
            print_info "Building Docker image..."
            docker build -f docker/Dockerfile.gutenocr -t gutenocr:cpu-latest .
        fi
        
        # Stop existing container if running
        if docker ps -a | grep -q "gutenocr-cpu"; then
            print_info "Stopping existing container..."
            docker stop gutenocr-cpu 2>/dev/null || true
            docker rm gutenocr-cpu 2>/dev/null || true
        fi
        
        # Run container
        print_info "Starting container..."
        docker run -d \
            --name gutenocr-cpu \
            -p 7860:7860 \
            -v "$(pwd)/input:/app/input" \
            -v "$(pwd)/output:/app/output" \
            gutenocr:cpu-latest
        
        print_info "Container started. Access UI at http://localhost:7860"
        print_info "View logs with: docker logs -f gutenocr-cpu"
        ;;
    
    docker-gpu)
        print_info "Starting GutenOCR with Docker (GPU)..."
        
        # Check for NVIDIA Docker runtime
        if ! docker info 2>/dev/null | grep -q "nvidia"; then
            print_error "NVIDIA Docker runtime not found. Please install nvidia-docker2"
            exit 1
        fi
        
        # Build image if it doesn't exist
        if ! docker images | grep -q "gutenocr.*gpu"; then
            print_info "Building Docker image..."
            docker build -f docker/Dockerfile.gutenocr-gpu -t gutenocr:gpu-latest .
        fi
        
        # Stop existing container if running
        if docker ps -a | grep -q "gutenocr-gpu"; then
            print_info "Stopping existing container..."
            docker stop gutenocr-gpu 2>/dev/null || true
            docker rm gutenocr-gpu 2>/dev/null || true
        fi
        
        # Run container with GPU
        print_info "Starting container with GPU..."
        docker run -d \
            --name gutenocr-gpu \
            --gpus all \
            -p 7860:7860 \
            -v "$(pwd)/input:/app/input" \
            -v "$(pwd)/output:/app/output" \
            gutenocr:gpu-latest
        
        print_info "Container started. Access UI at http://localhost:7860"
        print_info "View logs with: docker logs -f gutenocr-gpu"
        ;;
    
    k8s)
        print_info "Deploying to Kubernetes..."
        
        # Check if kubectl is available
        if ! command -v kubectl &> /dev/null; then
            print_error "kubectl not found. Please install kubectl"
            exit 1
        fi
        
        # Apply Kubernetes configurations
        print_info "Creating persistent volumes..."
        kubectl apply -f kubernetes/persistent-volumes.yaml
        
        print_info "Creating config maps..."
        kubectl apply -f kubernetes/configmap.yaml
        
        print_info "Deploying CPU version..."
        kubectl apply -f kubernetes/deployment-cpu.yaml
        
        print_info "Deploying GPU version..."
        kubectl apply -f kubernetes/deployment-gpu.yaml
        
        print_info "Creating ingress..."
        kubectl apply -f kubernetes/ingress.yaml
        
        print_info "Deployment complete!"
        print_info "Check status with: kubectl get pods -l app=gutenocr"
        ;;
    
    *)
        print_error "Unknown mode: $MODE"
        echo "Use --help for usage information"
        exit 1
        ;;
esac

print_info "Startup complete!"

# Made with Bob
