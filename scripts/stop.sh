#!/bin/bash

# GutenOCR Stop Script
# This script stops the GutenOCR application

set -e

echo "=========================================="
echo "GutenOCR Application Shutdown"
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

# Parse command line arguments
MODE="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./scripts/stop.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE    Stop mode: all, docker, k8s, local"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

stop_docker() {
    print_info "Stopping Docker containers..."
    
    # Stop CPU container
    if docker ps -a | grep -q "gutenocr-cpu"; then
        print_info "Stopping gutenocr-cpu..."
        docker stop gutenocr-cpu 2>/dev/null || true
        docker rm gutenocr-cpu 2>/dev/null || true
    fi
    
    # Stop GPU container
    if docker ps -a | grep -q "gutenocr-gpu"; then
        print_info "Stopping gutenocr-gpu..."
        docker stop gutenocr-gpu 2>/dev/null || true
        docker rm gutenocr-gpu 2>/dev/null || true
    fi
    
    # Stop combined container
    if docker ps -a | grep -q "combined-processor"; then
        print_info "Stopping combined-processor..."
        docker stop combined-processor 2>/dev/null || true
        docker rm combined-processor 2>/dev/null || true
    fi
    
    # Stop docker-compose services
    if [ -f "docker/docker-compose.yml" ]; then
        print_info "Stopping docker-compose services..."
        cd docker && docker-compose down 2>/dev/null || true
        cd ..
    fi
    
    print_info "Docker containers stopped"
}

stop_k8s() {
    print_info "Stopping Kubernetes deployments..."
    
    # Check if kubectl is available
    if ! command -v kubectl &> /dev/null; then
        print_warning "kubectl not found. Skipping Kubernetes cleanup"
        return
    fi
    
    # Delete deployments
    print_info "Deleting deployments..."
    kubectl delete -f kubernetes/deployment-cpu.yaml --ignore-not-found=true
    kubectl delete -f kubernetes/deployment-gpu.yaml --ignore-not-found=true
    
    # Delete services
    print_info "Deleting services..."
    kubectl delete service gutenocr-cpu-service --ignore-not-found=true
    kubectl delete service gutenocr-gpu-service --ignore-not-found=true
    
    # Delete ingress
    print_info "Deleting ingress..."
    kubectl delete -f kubernetes/ingress.yaml --ignore-not-found=true
    
    # Optionally delete PVCs (commented out to preserve data)
    # print_warning "Persistent volumes are preserved. To delete them, run:"
    # echo "kubectl delete -f kubernetes/persistent-volumes.yaml"
    
    print_info "Kubernetes resources deleted"
}

stop_local() {
    print_info "Stopping local processes..."
    
    # Find and kill Python processes running GutenOCR
    PIDS=$(ps aux | grep -E "python.*gradio_ui.py|python.*docling_gutenocr_combined.py" | grep -v grep | awk '{print $2}')
    
    if [ -z "$PIDS" ]; then
        print_info "No local GutenOCR processes found"
    else
        for PID in $PIDS; do
            print_info "Stopping process $PID..."
            kill -15 $PID 2>/dev/null || true
            sleep 2
            # Force kill if still running
            if ps -p $PID > /dev/null 2>&1; then
                print_warning "Force killing process $PID..."
                kill -9 $PID 2>/dev/null || true
            fi
        done
        print_info "Local processes stopped"
    fi
}

case $MODE in
    all)
        print_info "Stopping all GutenOCR instances..."
        stop_local
        stop_docker
        stop_k8s
        ;;
    
    docker)
        stop_docker
        ;;
    
    k8s)
        stop_k8s
        ;;
    
    local)
        stop_local
        ;;
    
    *)
        print_error "Unknown mode: $MODE"
        echo "Use --help for usage information"
        exit 1
        ;;
esac

print_info "Shutdown complete!"

# Made with Bob
