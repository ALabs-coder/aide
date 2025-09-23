#!/bin/bash
set -e

# PDF Extractor API - Master Build Script
# This script builds both Lambda layers and functions

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
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

log_header() {
    echo -e "${BOLD}${BLUE}$1${NC}"
    echo -e "${BLUE}$(printf '=%.0s' {1..60})${NC}"
}

# Build everything
build_all() {
    log_header "PDF Extractor API - Lambda Build Process"
    
    # Check and activate Python virtual environment
    local venv_path="$(cd "$SCRIPT_DIR/../.." && pwd)/api/api_env"
    if [[ -f "$venv_path/bin/activate" ]]; then
        log_info "Activating Python virtual environment..."
        source "$venv_path/bin/activate"
        log_success "Virtual environment activated"
    else
        log_warning "Virtual environment not found at $venv_path"
        log_info "Trying to use system Python/pip..."
    fi
    
    # Build layers first
    log_header "Step 1: Building Lambda Layers"
    if bash "$SCRIPT_DIR/build-layers.sh"; then
        log_success "Lambda layers built successfully"
    else
        log_error "Failed to build Lambda layers"
        exit 1
    fi
    
    echo
    
    # Build functions
    log_header "Step 2: Building Lambda Functions"
    if bash "$SCRIPT_DIR/build-functions.sh"; then
        log_success "Lambda functions built successfully"
    else
        log_error "Failed to build Lambda functions"
        exit 1
    fi
    
    echo
    
    # Summary
    log_header "Build Complete - Summary"
    
    local layers_dir="$(cd "$SCRIPT_DIR/.." && pwd)/lambda_packages/layers"
    local functions_dir="$(cd "$SCRIPT_DIR/.." && pwd)/lambda_packages/functions"
    
    log_info "Lambda Layers:"
    if [[ -d "$layers_dir" ]]; then
        ls -lh "$layers_dir"/*.zip 2>/dev/null | while read -r line; do
            log_info "  $(echo "$line" | awk '{print $9 " - " $5}' | sed 's|.*/||')"
        done
    fi
    
    log_info "Lambda Functions:"
    if [[ -d "$functions_dir" ]]; then
        ls -lh "$functions_dir"/*.zip 2>/dev/null | while read -r line; do
            log_info "  $(echo "$line" | awk '{print $9 " - " $5}' | sed 's|.*/||')"
        done
    fi
    
    echo
    log_success "🚀 All Lambda packages ready for deployment!"
    log_info "Next step: Run 'terraform apply' to deploy to AWS"
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    build_all
fi