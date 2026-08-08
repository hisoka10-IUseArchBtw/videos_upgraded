#!/usr/bin/env bash
# =============================================================================
#  deploy.sh — Apply all K8s manifests in dependency order
#  Usage: ./infrastructure/kubernetes/deploy.sh [--dry-run]
# =============================================================================
set -euo pipefail

K8S_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRY_RUN=""

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN="--dry-run=client"
  echo "🔍 DRY RUN MODE — no resources will be created"
fi

KUBECTL="kubectl $DRY_RUN"

echo ""
echo "🚀 Deploying Video Understanding Engine to Kubernetes"
echo "======================================================="

# 1. Namespace first
echo "📦 [1/7] Creating namespace..."
$KUBECTL apply -f "$K8S_DIR/namespace.yaml"

# 2. Secrets & ConfigMaps (must exist before pods reference them)
echo "🔐 [2/7] Applying secrets & configmaps..."
$KUBECTL apply -f "$K8S_DIR/secrets/secrets.yaml"
$KUBECTL apply -f "$K8S_DIR/configmaps/app-config.yaml"

# 3. Stateful services (databases & storage)
echo "🗄️  [3/7] Deploying stateful services (postgres, redis, qdrant, minio)..."
$KUBECTL apply -f "$K8S_DIR/postgres/"
$KUBECTL apply -f "$K8S_DIR/redis/"
$KUBECTL apply -f "$K8S_DIR/qdrant/"
$KUBECTL apply -f "$K8S_DIR/minio/"

# 4. Wait for databases to be ready
if [[ -z "$DRY_RUN" ]]; then
  echo "⏳ Waiting for postgres to be ready..."
  kubectl rollout status statefulset/postgres -n video-engine --timeout=120s

  echo "⏳ Waiting for redis to be ready..."
  kubectl rollout status deployment/redis -n video-engine --timeout=60s

  echo "⏳ Waiting for qdrant to be ready..."
  kubectl rollout status statefulset/qdrant -n video-engine --timeout=120s
fi

# 5. Application pods
echo "🐍 [4/7] Deploying API and worker..."
$KUBECTL apply -f "$K8S_DIR/api/"
$KUBECTL apply -f "$K8S_DIR/worker/"

# 6. Monitoring
echo "📊 [5/7] Deploying monitoring stack (Prometheus + Grafana)..."
$KUBECTL apply -f "$K8S_DIR/monitoring/"

# 7. Ingress
echo "🌐 [6/7] Applying ingress rules..."
$KUBECTL apply -f "$K8S_DIR/ingress/"

echo ""
echo "✅ All manifests applied!"
echo ""
echo "📋 Resource status:"
kubectl get all -n video-engine 2>/dev/null || true

echo ""
echo "🔗 Next steps:"
echo "  1. Check pods: kubectl get pods -n video-engine -w"
echo "  2. View logs:  kubectl logs -f deployment/api -n video-engine"
echo "  3. Port forward for local testing:"
echo "     kubectl port-forward svc/api 8000:8000 -n video-engine"
echo "     kubectl port-forward svc/grafana 3001:3000 -n video-engine"
