#!/bin/bash
set -e

# PDF Extractor API - Lambda Functions Build Script
# This script builds Lambda function packages (without dependencies - using layers)

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INFRA_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
API_ROOT="$PROJECT_ROOT/api"
FUNCTIONS_DIR="$API_ROOT/lambdas"
OUTPUT_DIR="$INFRA_ROOT/lambda_packages/functions"

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

# Clean output directory
clean_output() {
    log_info "Cleaning functions output directory..."
    rm -rf "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
    log_success "Functions output directory cleaned"
}

# Build individual Lambda function
build_function() {
    local function_name=$1
    local function_dir="$FUNCTIONS_DIR/$function_name"
    local build_dir="$OUTPUT_DIR/${function_name}-build"
    
    log_info "Building Lambda function: $function_name"
    
    # Check if function directory exists
    if [[ ! -d "$function_dir" ]]; then
        log_error "Function directory not found: $function_dir"
        return 1
    fi
    
    # Create build directory
    mkdir -p "$build_dir"
    
    # Copy function handler
    if [[ -f "$function_dir/handler.py" ]]; then
        cp "$function_dir/handler.py" "$build_dir/"
        log_info "  Copied handler.py"
    else
        log_error "  handler.py not found in $function_dir"
        return 1
    fi

    # Special handling for processor function - include extractors and main extraction file
    if [[ "$function_name" == "processor" ]]; then
        # Copy extractors directory if it exists
        if [[ -d "$API_ROOT/extractors" ]]; then
            cp -r "$API_ROOT/extractors" "$build_dir/"
            log_info "  Copied extractors directory"
        fi

        # Copy main extraction file
        if [[ -f "$API_ROOT/extract_pdf_data.py" ]]; then
            cp "$API_ROOT/extract_pdf_data.py" "$build_dir/"
            log_info "  Copied extract_pdf_data.py"
        fi
    fi

    # Special handling for functions that need formatters directory
    if [[ "$function_name" == "excel_export" || "$function_name" == "statement_data" ]]; then
        # Copy formatters directory if it exists
        if [[ -d "$API_ROOT/formatters" ]]; then
            cp -r "$API_ROOT/formatters" "$build_dir/"
            log_info "  Copied formatters directory"
        fi
    fi
    
    # Copy any additional function-specific files
    if [[ -f "$function_dir/requirements.txt" ]]; then
        cp "$function_dir/requirements.txt" "$build_dir/"
        log_info "  Copied function-specific requirements.txt"
    fi
    
    # Create zip file
    log_info "  Creating function zip file..."
    cd "$build_dir"
    zip -r9 "$OUTPUT_DIR/${function_name}.zip" . > /dev/null
    cd - > /dev/null
    
    # Cleanup build directory
    rm -rf "$build_dir"
    
    local zip_size=$(du -h "$OUTPUT_DIR/${function_name}.zip" | cut -f1)
    log_success "  Function package created: ${function_name}.zip (${zip_size})"
}

# Build all Lambda functions
build_all_functions() {
    log_info "Starting Lambda functions build process..."
    
    clean_output
    
    # List of Lambda functions to build
    local functions=("api" "upload" "statement_data" "excel_export" "processor" "cleanup" "dlq_processor" "pdf_viewer")
    
    for function_name in "${functions[@]}"; do
        build_function "$function_name"
    done
    
    log_info "Build summary:"
    ls -lh "$OUTPUT_DIR"/*.zip | while read -r line; do
        log_info "  $(echo "$line" | awk '{print $9 " - " $5}')"
    done
    
    log_success "All Lambda functions built successfully!"
    log_info "Function packages are available in: $OUTPUT_DIR"
}

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    build_all_functions
fi