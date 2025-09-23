#!/bin/bash
set -e

# PDF Extractor API - Docker-based Lambda Layers Build Script
# This script builds Lambda layers using Docker to ensure Linux x86_64 compatibility

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INFRA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_ROOT="$PROJECT_ROOT/api"
LAYERS_DIR="$INFRA_ROOT/layers"
OUTPUT_DIR="$INFRA_ROOT/lambda_packages/layers"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not found. Please install Docker."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi

    log_success "All prerequisites met"
}

# Clean output directory
clean_output() {
    log_info "Cleaning output directory..."
    rm -rf "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
    log_success "Output directory cleaned"
}

# Build common dependencies layer using Docker
build_common_layer_docker() {
    log_info "Building common dependencies layer using Docker..."

    local layer_name="pdf-extractor-common"
    local layer_dir="$LAYERS_DIR/common-dependencies"

    # Use AWS Lambda Python runtime image
    docker run --rm \
        -v "$layer_dir:/requirements" \
        -v "$OUTPUT_DIR:/output" \
        public.ecr.aws/lambda/python:3.11 \
        bash -c "
            mkdir -p /tmp/layer/python
            pip install -r /requirements/requirements.txt -t /tmp/layer/python --no-cache-dir
            # Remove unnecessary files to reduce size
            find /tmp/layer/python -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
            find /tmp/layer/python -type d -name '*.dist-info' -exec rm -rf {} + 2>/dev/null || true
            find /tmp/layer/python -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true
            find /tmp/layer/python -name '*.pyc' -delete 2>/dev/null || true
            find /tmp/layer/python -name '*.pyo' -delete 2>/dev/null || true
            cd /tmp/layer
            zip -r9 /output/${layer_name}.zip python/
        "

    local zip_size=$(du -h "$OUTPUT_DIR/${layer_name}.zip" | cut -f1)
    log_success "Common dependencies layer created: ${layer_name}.zip (${zip_size})"
}

# Build API dependencies layer using Docker
build_api_layer_docker() {
    log_info "Building API dependencies layer using Docker..."

    local layer_name="pdf-extractor-api"
    local layer_dir="$LAYERS_DIR/api-dependencies"

    # Use AWS Lambda Python runtime image
    docker run --rm \
        -v "$layer_dir:/requirements" \
        -v "$OUTPUT_DIR:/output" \
        public.ecr.aws/lambda/python:3.11 \
        bash -c "
            mkdir -p /tmp/layer/python
            pip install -r /requirements/requirements.txt -t /tmp/layer/python --no-cache-dir
            # Remove unnecessary files to reduce size
            find /tmp/layer/python -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
            find /tmp/layer/python -type d -name '*.dist-info' -exec rm -rf {} + 2>/dev/null || true
            find /tmp/layer/python -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true
            find /tmp/layer/python -name '*.pyc' -delete 2>/dev/null || true
            find /tmp/layer/python -name '*.pyo' -delete 2>/dev/null || true
            cd /tmp/layer
            zip -r9 /output/${layer_name}.zip python/
        "

    local zip_size=$(du -h "$OUTPUT_DIR/${layer_name}.zip" | cut -f1)
    log_success "API dependencies layer created: ${layer_name}.zip (${zip_size})"
}

# Build business logic layer (no Docker needed as it's just Python files)
build_business_layer() {
    log_info "Building business logic layer..."

    local layer_name="pdf-extractor-business"
    local layer_dir="$LAYERS_DIR/business-logic"
    local build_dir="$OUTPUT_DIR/${layer_name}-build"
    local python_dir="$build_dir/python"

    # Create build directory
    mkdir -p "$python_dir"

    # Install dependencies if requirements.txt exists using Docker
    if [[ -f "$layer_dir/requirements.txt" ]]; then
        local site_packages_dir="$python_dir/lib/python3.11/site-packages"
        mkdir -p "$site_packages_dir"
        log_info "Installing business logic dependencies using Docker..."

        docker run --rm \
            -v "$layer_dir:/requirements" \
            -v "$site_packages_dir:/output" \
            public.ecr.aws/lambda/python:3.11 \
            bash -c "
                pip install -r /requirements/requirements.txt -t /output --no-cache-dir
                # Remove unnecessary files to reduce size
                find /output -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
                find /output -type d -name '*.dist-info' -exec rm -rf {} + 2>/dev/null || true
                find /output -name '*.pyc' -delete 2>/dev/null || true
            "
    fi

    # Copy business logic modules
    log_info "Copying business logic modules..."
    cp "$API_ROOT/config.py" "$python_dir/"
    cp "$API_ROOT/logging_config.py" "$python_dir/"
    cp "$API_ROOT/extract_pdf_data.py" "$python_dir/"

    # Create __init__.py files to make it a proper Python package
    touch "$python_dir/__init__.py"

    # Create zip file
    log_info "Creating layer zip file..."
    cd "$build_dir"
    zip -r9 "$OUTPUT_DIR/${layer_name}.zip" python/ > /dev/null
    cd - > /dev/null

    # Cleanup build directory
    rm -rf "$build_dir"

    local zip_size=$(du -h "$OUTPUT_DIR/${layer_name}.zip" | cut -f1)
    log_success "Business logic layer created: ${layer_name}.zip (${zip_size})"
}

# Build all layers using Docker
build_all_layers_docker() {
    log_info "Starting Docker-based Lambda layers build process..."

    check_prerequisites
    clean_output

    build_common_layer_docker
    build_api_layer_docker
    build_business_layer

    log_info "Build summary:"
    ls -lh "$OUTPUT_DIR"/*.zip | while read -r line; do
        log_info "  $(echo "$line" | awk '{print $9 " - " $5}')"
    done

    log_success "All Lambda layers built successfully using Docker!"
    log_info "Layer files are available in: $OUTPUT_DIR"
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    build_all_layers_docker
fi