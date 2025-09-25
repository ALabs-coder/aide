# Enhanced PDF Recognition and Bank Detection Plan

## Executive Summary
This plan addresses the current limitations in PDF processing where unrecognizable PDFs fail without proper error classification or user guidance. The implementation will add robust PDF validation, multi-bank support, and intelligent error handling.

## Current State Analysis

### Existing Issues
1. **Single Bank Support**: Only Union Bank extractor implemented
2. **No Bank Detection**: System defaults to Union Bank for all PDFs
3. **Generic Error Messages**: Users don't understand why extraction failed
4. **No PDF Content Validation**: System doesn't check if PDF contains extractable text
5. **Limited Error Recovery**: Failed PDFs provide no actionable guidance

### Current Architecture
```
PDF Upload → S3 Storage → SQS Queue → Processor Lambda → Union Bank Extractor
                                              ↓
                                        (Fails for non-Union Bank PDFs)
```

## Proposed Enhancement Architecture

```
PDF Upload → Validation Layer → Bank Detection → Router → Bank-Specific Extractor
              ↓                      ↓              ↓              ↓
         Error Classification   Confidence Score  Dynamic     Success/Detailed Error
```

## Implementation Phases

## Phase 1: PDF Validation & Recognition Layer (Week 1)

### 1.1 Create PDF Validator Module
**File**: `api/validators/pdf_validator.py`

```python
class PDFValidator:
    def validate(self, pdf_path: str) -> ValidationResult:
        """
        Returns:
        - is_valid: bool
        - pdf_type: 'text' | 'scanned' | 'hybrid'
        - error_code: str
        - error_message: str
        - metadata: dict
        """
```

**Validation Checks**:
- PDF structure integrity
- Text content availability
- Encryption status
- File corruption detection
- Minimum page count
- File size within limits

### 1.2 Error Classification System
**File**: `api/validators/error_codes.py`

```python
ERROR_CODES = {
    'INVALID_PDF': 'The file appears to be corrupted or is not a valid PDF',
    'SCANNED_PDF': 'This PDF contains scanned images without extractable text',
    'WRONG_BANK': 'This statement format is not recognized. Supported banks: {banks}',
    'ENCRYPTED_NO_PASSWORD': 'PDF is password protected but no password provided',
    'WRONG_PASSWORD': 'The provided password is incorrect',
    'NO_TRANSACTIONS': 'No transaction data found in the PDF',
    'UNSUPPORTED_FORMAT': 'This PDF format is not currently supported'
}
```

## Phase 2: Bank Detection System (Week 1-2)

### 2.1 Bank Detector Module
**File**: `api/extractors/bank_detector.py`

```python
class BankDetector:
    def detect_bank(self, pdf_path: str, password: str = None) -> BankDetectionResult:
        """
        Returns:
        - bank_name: str
        - confidence_score: float (0-1)
        - detection_method: 'keyword' | 'pattern' | 'logo' | 'user_provided'
        - alternative_banks: List[str]
        """
```

**Detection Methods**:
1. **Keyword Matching**: Search for bank names, IFSC codes, bank-specific terms
2. **Pattern Recognition**: Identify transaction table structures unique to each bank
3. **Logo Detection**: Use image recognition for bank logos (future)
4. **Metadata Analysis**: Check PDF properties and creator information

### 2.2 Supported Banks Configuration
**File**: `api/config/supported_banks.py`

```python
SUPPORTED_BANKS = {
    'union_bank': {
        'name': 'Union Bank of India',
        'keywords': ['Union Bank', 'UBIN'],
        'extractor': 'UnionBankExtractor',
        'patterns': [...]
    },
    'hdfc': {
        'name': 'HDFC Bank',
        'keywords': ['HDFC Bank', 'HDFC0'],
        'extractor': 'HDFCBankExtractor',
        'patterns': [...]
    },
    'icici': {
        'name': 'ICICI Bank',
        'keywords': ['ICICI Bank', 'ICIC0'],
        'extractor': 'ICICIBankExtractor',
        'patterns': [...]
    },
    'sbi': {
        'name': 'State Bank of India',
        'keywords': ['State Bank', 'SBIN0'],
        'extractor': 'SBIExtractor',
        'patterns': [...]
    },
    'axis': {
        'name': 'Axis Bank',
        'keywords': ['Axis Bank', 'UTIB0'],
        'extractor': 'AxisBankExtractor',
        'patterns': [...]
    }
}
```

## Phase 3: Multi-Bank Extractor Framework (Week 2-3)

### 3.1 Base Extractor Class
**File**: `api/extractors/base_extractor.py`

```python
class BaseBankExtractor(ABC):
    """Abstract base class for all bank extractors"""

    @abstractmethod
    def extract_statement_metadata(self, text: str) -> Dict:
        """Extract account details, period, etc."""
        pass

    @abstractmethod
    def extract_transactions(self, pdf_reader) -> List[Dict]:
        """Extract transaction records"""
        pass

    @abstractmethod
    def validate_extraction(self, transactions: List[Dict]) -> bool:
        """Validate extracted data integrity"""
        pass

    # Common utilities
    def parse_date(self, date_str: str) -> datetime:
        """Parse various date formats"""
        pass

    def parse_amount(self, amount_str: str) -> Decimal:
        """Parse amount with various formats"""
        pass

    def normalize_transaction(self, raw_transaction: Dict) -> Dict:
        """Normalize to standard format"""
        pass
```

### 3.2 Bank-Specific Extractors
**Files**:
- `api/extractors/hdfc_extractor.py`
- `api/extractors/icici_extractor.py`
- `api/extractors/sbi_extractor.py`
- `api/extractors/axis_extractor.py`

Each extractor will:
1. Inherit from `BaseBankExtractor`
2. Implement bank-specific parsing logic
3. Handle bank-specific date/amount formats
4. Extract bank-specific metadata fields

## Phase 4: Enhanced Processing Pipeline (Week 3)

### 4.1 Updated Processor Lambda
**File**: `api/lambdas/processor/handler.py`

```python
def process_pdf_with_validation(pdf_path: str, password: str = None):
    # Step 1: Validate PDF
    validation_result = PDFValidator().validate(pdf_path)
    if not validation_result.is_valid:
        return create_error_response(validation_result)

    # Step 2: Detect Bank
    bank_result = BankDetector().detect_bank(pdf_path, password)
    if bank_result.confidence_score < 0.6:
        return request_user_bank_selection(bank_result.alternative_banks)

    # Step 3: Get appropriate extractor
    extractor = ExtractorFactory.get_extractor(bank_result.bank_name)

    # Step 4: Extract data
    try:
        extraction_result = extractor.extract_complete_statement(pdf_path, password)
        return create_success_response(extraction_result)
    except ExtractionError as e:
        return create_extraction_error_response(e)
```

### 4.2 Extractor Factory Pattern
**File**: `api/extractors/extractor_factory.py`

```python
class ExtractorFactory:
    @staticmethod
    def get_extractor(bank_name: str) -> BaseBankExtractor:
        """Return appropriate extractor instance for the bank"""
        extractors = {
            'union_bank': UnionBankExtractor,
            'hdfc': HDFCBankExtractor,
            'icici': ICICIBankExtractor,
            'sbi': SBIExtractor,
            'axis': AxisBankExtractor
        }

        if bank_name not in extractors:
            raise UnsupportedBankError(f"Bank {bank_name} is not supported")

        return extractors[bank_name]()
```

## Phase 5: OCR Support for Scanned PDFs (Week 4 - Optional)

### 5.1 OCR Integration
**File**: `api/services/ocr_service.py`

```python
class OCRService:
    def __init__(self):
        self.textract_client = boto3.client('textract')

    def extract_text_from_scanned_pdf(self, pdf_path: str) -> str:
        """Use AWS Textract for OCR"""
        pass

    def preprocess_for_ocr(self, pdf_path: str) -> str:
        """Enhance image quality for better OCR"""
        pass
```

### 5.2 Configuration
Add to Lambda environment variables:
- `ENABLE_OCR`: true/false
- `OCR_CONFIDENCE_THRESHOLD`: 0.8
- `MAX_OCR_PAGES`: 50

## Phase 6: User Experience Enhancements (Week 4)

### 6.1 Enhanced Upload API
**Endpoint**: `POST /upload`

New optional parameters:
```json
{
    "file": "...",
    "password": "...",
    "bank_hint": "hdfc",  // Optional bank hint
    "enable_ocr": false   // Optional OCR flag
}
```

### 6.2 Enhanced Job Status
**DynamoDB Schema Updates**:
```json
{
    "job_id": "...",
    "status": "processing",
    "validation_status": {
        "is_valid": true,
        "pdf_type": "text",
        "warnings": []
    },
    "bank_detection": {
        "detected_bank": "hdfc",
        "confidence": 0.92,
        "method": "keyword"
    },
    "error_details": {
        "code": "WRONG_BANK",
        "message": "...",
        "suggestions": ["Try selecting the bank manually", "..."]
    }
}
```

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Phase 1 | PDF Validator, Error Classification |
| 1-2 | Phase 2 | Bank Detection System |
| 2-3 | Phase 3 | Multi-Bank Extractors |
| 3 | Phase 4 | Enhanced Pipeline Integration |
| 4 | Phase 5-6 | OCR Support, UX Improvements |

## Testing Strategy

### Unit Tests
- Test each validator with various PDF types
- Test bank detection with sample statements
- Test each bank extractor individually

### Integration Tests
- End-to-end testing with real bank statements
- Error scenario testing (corrupt, wrong bank, scanned)
- Performance testing with large PDFs

### Test Data Requirements
- Sample PDFs from each supported bank
- Corrupted PDF samples
- Scanned PDF samples
- Password-protected samples

## Monitoring & Success Metrics

### Key Metrics to Track
1. **Validation Success Rate**: % of PDFs passing validation
2. **Bank Detection Accuracy**: % correctly identified
3. **Extraction Success Rate**: % successful extractions per bank
4. **Error Classification Distribution**: Breakdown by error type
5. **Processing Time**: Average time per PDF

### CloudWatch Dashboards
- Real-time processing status
- Error rate trends
- Bank distribution analytics
- Performance metrics

### Alerts
- High failure rate (>20% in 5 minutes)
- Unknown bank detection (>10 in 1 hour)
- OCR service failures
- Processing queue backup

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Bank format changes | Extraction failures | Version-aware extractors, regular updates |
| OCR accuracy issues | Poor data quality | Confidence thresholds, manual review option |
| Performance degradation | Slow processing | Caching, parallel processing, resource optimization |
| Unsupported bank uploaded | User frustration | Clear error messages, request form for new banks |

## Security Considerations

1. **PDF Validation**: Prevent malicious PDF uploads
2. **Password Handling**: Secure storage and transmission
3. **OCR Data**: Ensure PII is not logged
4. **Error Messages**: Don't expose sensitive system details

## Rollback Strategy

1. Feature flags for gradual rollout
2. Keep existing Union Bank extractor as fallback
3. Version-tagged Lambda deployments
4. Database migration scripts with rollback capability

## Future Enhancements

1. **Machine Learning Bank Detection**: Train model on statement patterns
2. **Multi-language Support**: Handle regional language statements
3. **Credit Card Statement Support**: Extend beyond bank statements
4. **Batch Processing**: Handle multiple PDFs in single request
5. **Webhook Notifications**: Real-time processing updates
6. **API for Bank Format Updates**: Allow dynamic format configuration

## Questions Requiring Clarification

1. **Priority Banks**: Which banks should be implemented first after Union Bank?
2. **OCR Budget**: Is AWS Textract within budget for OCR processing?
3. **Error Handling**: Should failed PDFs be retained for manual review?
4. **User Selection**: Should users be required to select their bank upfront?
5. **Confidence Threshold**: What confidence level triggers manual bank selection?
6. **Regional Banks**: Should we support regional/cooperative banks?
7. **Statement Types**: Focus only on savings accounts or include current/credit accounts?

## Success Criteria

- ✅ 95% of valid PDFs are correctly validated
- ✅ 90% bank detection accuracy for supported banks
- ✅ Clear error messages for all failure scenarios
- ✅ Support for top 5 Indian banks
- ✅ Processing time under 10 seconds per PDF
- ✅ Zero data loss during extraction
- ✅ Comprehensive monitoring and alerting

## Conclusion

This enhancement plan transforms the PDF processing system from a single-bank solution to a robust, multi-bank platform with intelligent error handling and user guidance. The phased approach ensures minimal disruption while progressively adding capabilities.

The implementation focuses on:
1. **Reliability**: Proper validation and error handling
2. **Scalability**: Support for multiple banks with easy addition of new ones
3. **User Experience**: Clear feedback and guidance
4. **Maintainability**: Modular design with shared components

Upon completion, the system will gracefully handle any PDF type, provide clear feedback for issues, and successfully process statements from major Indian banks.