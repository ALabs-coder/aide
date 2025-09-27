#!/bin/bash
set -e

# Python Minifier Helper Script
# Removes comments and docstrings from Python files for production deployment

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[MINIFY]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[MINIFY]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[MINIFY]${NC} $1"
}

log_error() {
    echo -e "${RED}[MINIFY]${NC} $1"
}

# Check if python-minifier is available
check_minifier() {
    # Check if python-minifier module is available
    if python3 -c "import python_minifier" &> /dev/null; then
        log_info "python-minifier module is available"
        return 0
    fi

    log_info "python-minifier not found, installing..."

    # Try different installation methods
    if command -v pip3 &> /dev/null; then
        pip3 install python-minifier --user --quiet 2>/dev/null || \
        pip3 install python-minifier --break-system-packages --quiet 2>/dev/null
    elif command -v pip &> /dev/null; then
        pip install python-minifier --user --quiet 2>/dev/null || \
        pip install python-minifier --break-system-packages --quiet 2>/dev/null
    fi

    # Check if installation was successful
    if python3 -c "import python_minifier" &> /dev/null; then
        log_success "python-minifier installed successfully"
    else
        log_error "Failed to install python-minifier"
        log_error "Please install manually: pip3 install python-minifier --break-system-packages"
        return 1
    fi
}

# Minify a single Python file
minify_file() {
    local input_file="$1"
    local temp_file="${input_file}.tmp"

    if [[ ! -f "$input_file" ]]; then
        log_warning "File not found: $input_file"
        return 1
    fi

    log_info "Minifying: $(basename "$input_file")"

    # Calculate original size
    local original_size=$(stat -f%z "$input_file" 2>/dev/null || stat -c%s "$input_file" 2>/dev/null || echo "0")

    # Minify the file (remove comments and docstrings, keep formatting readable)
    python3 -m python_minifier \
        --remove-literal-statements \
        --no-combine-imports \
        --no-remove-annotations \
        --output "$temp_file" \
        "$input_file"

    if [ $? -eq 0 ] && [ -s "$temp_file" ]; then
        # Calculate new size
        local new_size=$(stat -f%z "$temp_file" 2>/dev/null || stat -c%s "$temp_file" 2>/dev/null || echo "0")
        local reduction_percent=0

        if [ "$original_size" -gt 0 ]; then
            reduction_percent=$(( (original_size - new_size) * 100 / original_size ))
        fi

        # Replace original with minified version
        mv "$temp_file" "$input_file"
        log_success "  Reduced by ${reduction_percent}% (${original_size} → ${new_size} bytes)"
    else
        log_error "  Failed to minify, keeping original"
        rm -f "$temp_file"
        return 1
    fi
}

# Minify all Python files in a directory
minify_directory() {
    local target_dir="$1"

    if [[ ! -d "$target_dir" ]]; then
        log_warning "Directory not found: $target_dir"
        return 1
    fi

    log_info "Minifying Python files in: $target_dir"

    local file_count=0
    local success_count=0

    # Find all Python files and minify them
    while IFS= read -r -d '' file; do
        ((file_count++))
        if minify_file "$file"; then
            ((success_count++))
        fi
    done < <(find "$target_dir" -name "*.py" -type f -print0)

    if [ "$file_count" -eq 0 ]; then
        log_warning "No Python files found in $target_dir"
    else
        log_success "Minified $success_count/$file_count Python files in $(basename "$target_dir")"
    fi
}

# Main function
main() {
    local target="$1"

    if [[ -z "$target" ]]; then
        log_error "Usage: $0 <file_or_directory>"
        log_error "Examples:"
        log_error "  $0 /path/to/file.py"
        log_error "  $0 /path/to/directory"
        exit 1
    fi

    # Check prerequisites
    check_minifier || exit 1

    if [[ -f "$target" ]]; then
        # Single file
        minify_file "$target"
    elif [[ -d "$target" ]]; then
        # Directory
        minify_directory "$target"
    else
        log_error "Target not found: $target"
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi