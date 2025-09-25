# PDF Validator Tests

This directory contains comprehensive tests for the PDF Validator module.

## Running Tests

### Prerequisites
```bash
# Ensure you're in the project root directory
cd /path/to/aide

# Activate the Python virtual environment
source api/pdf_env/bin/activate
```

### Run All Tests
```bash
python tests/test_pdf_validator.py
```

### Expected Output
```
============================================================
PDF VALIDATOR TEST SUITE
============================================================
...
Test run: 17
Failures: 0
Errors: 0
============================================================
```

## Test Files Required

The tests use sample PDFs in the `test_pdfs/` directory:

- `valid_text.pdf` - Valid text-based PDF
- `corrupted.pdf` - Corrupted PDF file
- `scanned.pdf` - Scanned PDF without text
- `encrypted.pdf` - Password-protected PDF (password: `testpassword123`)
- `large_file.pdf` - File larger than 25MB
- `not_a_pdf.pdf` - Non-PDF file with .pdf extension
- `empty.pdf` - PDF with no pages
- `many_pages.pdf` - PDF with >200 pages

## Test Coverage

The test suite covers:
- ✅ Valid PDF validation
- ✅ File type detection (non-PDF files)
- ✅ Corrupted PDF handling
- ✅ Large file detection (>25MB)
- ✅ Encrypted PDF handling (with/without password)
- ✅ Scanned PDF detection
- ✅ Empty PDF detection
- ✅ Too many pages detection (>200)
- ✅ Performance requirements (<2 seconds)
- ✅ No side effects (files not modified)
- ✅ Error message formatting
- ✅ Boundary conditions

## Notes

- Error messages in the output for corrupted PDFs are expected (part of the test)
- All tests should pass (17/17)
- Tests use relative paths and will work in any environment