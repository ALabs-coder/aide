# Claude Code Hooks for Bank Statement Extractor

This directory contains Claude Code hooks that automatically integrate with the `bank-statement-extractor` agent to provide:

## 🎯 Hook Benefits

### 1. **Standardized Output Enforcement** (`output-validation.sh`)
- Validates consistent JSON structure across all bank extractors
- Ensures required fields: `total_transactions`, `statement_metadata`, `financial_summary`, `transactions`
- Checks transaction field completeness and format compliance
- Validates date format standardization (DD-MM-YYYY)

### 2. **Financial Accuracy Validation** (`financial-accuracy.sh`)
- Built-in balance calculation verification
- Mathematical consistency checks:
  - `net_change = total_credits - total_debits`
  - `closing_balance = opening_balance + net_change`
- Transaction count consistency across sections
- Currency standardization (INR) validation

### 3. **Automatic Agent Triggering** (`bank-extractor-trigger.sh`)
- Detects bank extraction tasks automatically
- Suggests using the bank-statement-extractor agent
- Provides contextual guidance for optimal extraction approach

## 🚀 Usage

### Automatic Activation
These hooks activate automatically when Claude Code detects:
- Bank statement processing tasks
- PDF extraction operations
- Financial data in outputs
- Keywords: "bank statement", "pdf extract", "canara bank", "union bank"

### Manual Testing
```bash
# Test bank extractor trigger
echo "I need to extract data from a Canara Bank PDF statement" | ./.claude/hooks/bank-extractor-trigger.sh

# Test output validation
echo '{"total_transactions": 10, "statement_metadata": {"bank_name": "Canara Bank"}}' | ./.claude/hooks/output-validation.sh

# Test financial accuracy
echo '{"opening_balance": 1000, "closing_balance": 1200, "total_credits": 300, "total_debits": 100, "net_change": 200}' | ./.claude/hooks/financial-accuracy.sh
```

## 🔧 Integration with Bank Statement Extractor Agent

These hooks complement the `bank-statement-extractor.md` agent by:

1. **Pre-Processing**: Automatically suggesting agent usage for relevant tasks
2. **Post-Processing**: Validating agent output for compliance and accuracy
3. **Quality Assurance**: Ensuring consistent output format across all bank extractors
4. **Financial Integrity**: Preventing calculation errors and data inconsistencies

## 📊 Validation Checklist

### Standardized Output ✅
- [ ] `total_transactions` field present and matches actual count
- [ ] `statement_metadata` with required bank info
- [ ] `financial_summary` with balance calculations
- [ ] `transactions` array with proper structure
- [ ] Date format: DD-MM-YYYY
- [ ] Transaction types: "Credit" or "Debit"

### Financial Accuracy ✅
- [ ] Opening balance + net change = closing balance
- [ ] Total credits - total debits = net change
- [ ] Transaction counts consistent across sections
- [ ] Currency set to "INR"
- [ ] Amounts in proper decimal format

## 🛠️ Hook Configuration

### Environment Variables
```bash
export CLAUDE_HOOKS_DIR="/Users/ramanjaneyulumedikonda/dev/aide/.claude/hooks"
export CLAUDE_AGENT_DIR="/Users/ramanjaneyulumedikonda/dev/aide/.claude/agents"
```

### Logging
Hooks log their activation to `~/.claude/hooks.log` for debugging and monitoring.

## 🎨 Customization

### Adding New Banks
1. Update `bank-extractor-trigger.sh` with new bank keywords
2. Add bank-specific validation rules to `output-validation.sh`
3. Extend financial accuracy checks for bank-specific formats

### Custom Validation Rules
Modify the validation scripts to add:
- Bank-specific field requirements
- Custom financial calculation rules
- Additional data integrity checks

## 📝 Examples

### Successful Validation Output
```
✅ STANDARDIZED OUTPUT STRUCTURE VALIDATED
✅ FINANCIAL SUMMARY FIELDS DETECTED
✅ BALANCE CALCULATIONS INCLUDED
✅ TRANSACTION TYPES PROPERLY CATEGORIZED
✅ DATE FORMAT STANDARDIZED (DD-MM-YYYY)
🎉 FINANCIAL ACCURACY VALIDATION PASSED
```

### Validation Failure Output
```
❌ STANDARDIZED OUTPUT VALIDATION FAILED
Missing required fields:
- total_transactions
- financial_summary

❌ NET CHANGE CALCULATION ERROR
Expected: 200.00, Got: 150.00

❌ BALANCE EQUATION ERROR
Opening (1000) + Net Change (150) ≠ Closing (1200)
```

## 🔗 Related Files

- `/api/validation_hooks.py` - Python validation implementation
- `/.claude/agents/bank-statement-extractor.md` - Specialized bank extraction agent
- `/api/extract_pdf_data.py` - Main extraction router
- `/api/extractors/` - Bank-specific extractor implementations

## 💡 Best Practices

1. **Always use the bank-statement-extractor agent** for bank PDF processing
2. **Import validation_hooks.py** in your Python extractors
3. **Use @validate_output decorator** for automatic validation
4. **Follow the standardized JSON schema** defined in the agent
5. **Test with multiple bank statement samples** before deployment

These hooks ensure that your bank statement extraction pipeline maintains high quality, consistency, and accuracy standards automatically.