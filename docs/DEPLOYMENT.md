# Deployment Guide

This guide covers all deployment options for the GutenOCR application.

## Table of Contents

- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Production Considerations](#production-considerations)

## Local Development

### Prerequisites

- Python 3.10+
- 8GB+ RAM (16GB+ recommended)
- (Optional) CUDA-capable GPU

### Setup

1. **Clone and Setup**
```bash
cd /Users/alainairom/Devs/GutenOCR-Test
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Start Application**
```bash
# Standard Gradio UI (OCR only)
./scripts/start.sh --mode gradio

# Docling + GutenOCR UI (NEW! - Advanced document processing)
./scripts/start.sh --mode docling-ui

# With CPU only
./scripts/start.sh --mode gradio --cpu
./scripts/start.sh --mode docling-ui --cpu

# With 7B model
./scripts/start.sh --mode gradio --model 7B
./scripts/start.sh --mode docling-ui --model 7B

# Combined processor (CLI)
./scripts/start.sh --mode combined
```

**Application URLs:**
- Standard UI: `http://localhost:7860`
- Docling + GutenOCR UI: `http://localhost:7861`

3. **Stop Application**
```bash
./scripts/stop.sh --mode local
```

## Docker Deployment

### Prerequisites

- Docker 20.10+
- (For GPU) NVIDIA Docker runtime
- 10GB+ disk space

### CPU Deployment

1. **Build Image**
```bash
docker build -f docker/Dockerfile.gutenocr -t gutenocr:cpu-latest .
```

2. **Run Container**
```bash
docker run -d \
    --name gutenocr-cpu \
    -p 7860:7860 \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    -v gutenocr-models:/root/.cache/huggingface \
    gutenocr:cpu-latest
```

3. **Access Application**
```
Standard UI: http://localhost:7860
Docling UI: http://localhost:7861 (if using combined image)
```

4. **View Logs**
```bash
docker logs -f gutenocr-cpu
```

5. **Stop Container**
```bash
docker stop gutenocr-cpu
docker rm gutenocr-cpu
```

### GPU Deployment

1. **Install NVIDIA Docker**
```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. **Build Image**
```bash
docker build -f docker/Dockerfile.gutenocr-gpu -t gutenocr:gpu-latest .
```

3. **Run Container**
```bash
docker run -d \
    --name gutenocr-gpu \
    --gpus all \
    -p 7860:7860 \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    -v gutenocr-models:/root/.cache/huggingface \
    gutenocr:gpu-latest
```

4. **Verify GPU Access**
```bash
docker exec gutenocr-gpu nvidia-smi
```

### Docker Compose

1. **Start Services**
```bash
cd docker

# CPU version
docker-compose up -d gutenocr-cpu

# GPU version
docker-compose up -d gutenocr-gpu

# Both
docker-compose up -d
```

2. **View Logs**
```bash
docker-compose logs -f gutenocr-cpu
```

3. **Stop Services**
```bash
docker-compose down
```

4. **Clean Up**
```bash
docker-compose down -v  # Remove volumes too
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster 1.20+
- kubectl configured
- 50GB+ storage
- (For GPU) NVIDIA GPU Operator

### Quick Deploy

```bash
./scripts/start.sh --mode k8s
```

### Manual Deployment

#### 1. Create Namespace (Optional)

```bash
kubectl create namespace gutenocr
kubectl config set-context --current --namespace=gutenocr
```

#### 2. Deploy Storage

```bash
kubectl apply -f kubernetes/persistent-volumes.yaml
```

Verify:
```bash
kubectl get pvc
```

#### 3. Deploy Configuration

```bash
kubectl apply -f kubernetes/configmap.yaml
```

#### 4. Deploy CPU Version

```bash
kubectl apply -f kubernetes/deployment-cpu.yaml
```

Verify:
```bash
kubectl get pods -l version=cpu
kubectl logs -f deployment/gutenocr-cpu
```

#### 5. Deploy GPU Version

**Install NVIDIA GPU Operator** (if not already installed):
```bash
helm repo add nvidia https://nvidia.github.io/gpu-operator
helm repo update
helm install gpu-operator nvidia/gpu-operator \
    --namespace gpu-operator-resources \
    --create-namespace
```

**Deploy GPU Application**:
```bash
kubectl apply -f kubernetes/deployment-gpu.yaml
```

Verify:
```bash
kubectl get pods -l version=gpu
kubectl logs -f deployment/gutenocr-gpu
```

#### 6. Setup Ingress

**Install Nginx Ingress Controller** (if not already installed):
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace
```

**Deploy Ingress**:
```bash
# Update ingress.yaml with your domain
kubectl apply -f kubernetes/ingress.yaml
```

#### 7. Access Application

```bash
# Get external IP
kubectl get ingress gutenocr-ingress

# Access via:
# http://your-domain.com/cpu  (CPU version)
# http://your-domain.com/gpu  (GPU version)
```

### Scaling

```bash
# Scale CPU deployment
kubectl scale deployment gutenocr-cpu --replicas=3

# Scale GPU deployment (limited by available GPUs)
kubectl scale deployment gutenocr-gpu --replicas=2

# Auto-scaling (HPA)
kubectl autoscale deployment gutenocr-cpu \
    --cpu-percent=70 \
    --min=2 \
    --max=10
```

### Monitoring

```bash
# Watch pods
kubectl get pods -l app=gutenocr -w

# View logs
kubectl logs -f deployment/gutenocr-cpu
kubectl logs -f deployment/gutenocr-gpu

# Describe pod
kubectl describe pod <pod-name>

# Execute commands in pod
kubectl exec -it <pod-name> -- bash
```

### Updating

```bash
# Update image
kubectl set image deployment/gutenocr-cpu \
    gutenocr=gutenocr:cpu-v2

# Rollout status
kubectl rollout status deployment/gutenocr-cpu

# Rollback
kubectl rollout undo deployment/gutenocr-cpu
```

### Cleanup

```bash
# Delete deployments
kubectl delete -f kubernetes/deployment-cpu.yaml
kubectl delete -f kubernetes/deployment-gpu.yaml

# Delete services
kubectl delete service gutenocr-cpu-service
kubectl delete service gutenocr-gpu-service

# Delete ingress
kubectl delete -f kubernetes/ingress.yaml

# Delete PVCs (optional - will delete data)
kubectl delete -f kubernetes/persistent-volumes.yaml

# Delete namespace (if created)
kubectl delete namespace gutenocr
```

## Production Considerations

### Security

1. **Enable HTTPS**
```yaml
# In ingress.yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - gutenocr.example.com
    secretName: gutenocr-tls
```

2. **Add Authentication**
```yaml
# Add to ingress annotations
nginx.ingress.kubernetes.io/auth-type: basic
nginx.ingress.kubernetes.io/auth-secret: basic-auth
nginx.ingress.kubernetes.io/auth-realm: 'Authentication Required'
```

3. **Network Policies**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gutenocr-netpol
spec:
  podSelector:
    matchLabels:
      app: gutenocr
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 7860
```

### Performance

1. **Resource Limits**
```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2000m"
  limits:
    memory: "8Gi"
    cpu: "4000m"
```

2. **Horizontal Pod Autoscaling**
```bash
kubectl autoscale deployment gutenocr-cpu \
    --cpu-percent=70 \
    --min=2 \
    --max=10
```

3. **Pod Disruption Budget**
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: gutenocr-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: gutenocr
```

### Monitoring

1. **Prometheus Metrics**
```yaml
# Add to deployment
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "7860"
  prometheus.io/path: "/metrics"
```

2. **Logging**
```bash
# Centralized logging with EFK stack
kubectl apply -f https://raw.githubusercontent.com/fluent/fluentd-kubernetes-daemonset/master/fluentd-daemonset-elasticsearch.yaml
```

### Backup

1. **Backup PVCs**
```bash
# Using Velero
velero backup create gutenocr-backup \
    --include-namespaces gutenocr \
    --wait
```

2. **Backup Configuration**
```bash
kubectl get all,pvc,configmap,secret -n gutenocr -o yaml > backup.yaml
```

### High Availability

1. **Multi-Zone Deployment**
```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - gutenocr
        topologyKey: topology.kubernetes.io/zone
```

2. **Multiple Replicas**
```bash
kubectl scale deployment gutenocr-cpu --replicas=3
```

### Cost Optimization

1. **Use Spot Instances** (for non-critical workloads)
```yaml
nodeSelector:
  node.kubernetes.io/instance-type: spot
tolerations:
- key: spot
  operator: Equal
  value: "true"
  effect: NoSchedule
```

2. **Resource Quotas**
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gutenocr-quota
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 40Gi
    limits.cpu: "20"
    limits.memory: 80Gi
```

## Troubleshooting

### Common Issues

1. **Pod Not Starting**
```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

2. **Out of Memory**
```bash
# Increase memory limits
kubectl edit deployment gutenocr-cpu
```

3. **GPU Not Available**
```bash
# Check GPU operator
kubectl get pods -n gpu-operator-resources

# Check node labels
kubectl get nodes --show-labels | grep nvidia
```

4. **Ingress Not Working**
```bash
# Check ingress controller
kubectl get pods -n ingress-nginx

# Check ingress
kubectl describe ingress gutenocr-ingress
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/YOUR_USERNAME/GutenOCR-Test/issues
- Documentation: https://github.com/YOUR_USERNAME/GutenOCR-Test/docs