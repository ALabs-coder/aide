#!/bin/bash
# Claude Code Hook: Bank Statement Output Validation
# Validates bank extractor output for standardized format and financial accuracy

# Hook Configuration
HOOK_NAME="output-validation"
VALIDATION_SCRIPT="/Users/ramanjaneyulumedikonda/dev/aide/api/validation_hooks.py"

# Function to check if output contains bank statement data
is_bank_output() {
    local content="$1"

    # Check for standardized bank output structure
    if echo "$content" | grep -q -E "(total_transactions|statement_metadata|financial_summary)" || \
       echo "$content" | grep -q -E "(bank_name|opening_balance|closing_balance)" || \
       echo "$content" | grep -q -E "(Transaction_Type|Credit|Debit)" || \
       echo "$content" | grep -iq -E "(canara bank|union bank)"; then
        return 0
    fi

    return 1
}

# Function to validate bank statement output
validate_output() {
    local content="$1"

    echo "🔍 BANK OUTPUT VALIDATION HOOK ACTIVATED"
    echo ""

    # Check for required standardized fields
    local missing_fields=""

    if ! echo "$content" | grep -q "total_transactions"; then
        missing_fields="${missing_fields}- total_transactions\n"
    fi

    if ! echo "$content" | grep -q "statement_metadata"; then
        missing_fields="${missing_fields}- statement_metadata\n"
    fi

    if ! echo "$content" | grep -q "financial_summary"; then
        missing_fields="${missing_fields}- financial_summary\n"
    fi

    if ! echo "$content" | grep -q "transactions"; then
        missing_fields="${missing_fields}- transactions\n"
    fi

    if [ -n "$missing_fields" ]; then
        echo "❌ STANDARDIZED OUTPUT VALIDATION FAILED"
        echo ""
        echo "Missing required fields:"
        echo -e "$missing_fields"
        echo "🎯 Ensure your extractor returns the standardized format defined in the bank-statement-extractor agent."
    else
        echo "✅ STANDARDIZED OUTPUT STRUCTURE VALIDATED"
    fi

    # Check for financial accuracy indicators
    echo ""
    if echo "$content" | grep -q -E "(opening_balance.*closing_balance|total_credits.*total_debits)"; then
        echo "✅ FINANCIAL SUMMARY FIELDS DETECTED"

        # Check for balance consistency indicators
        if echo "$content" | grep -q "net_change"; then
            echo "✅ BALANCE CALCULATIONS INCLUDED"
        else
            echo "⚠️  Consider adding net_change calculation for financial accuracy"
        fi
    else
        echo "❌ FINANCIAL ACCURACY VALIDATION INCOMPLETE"
        echo "   Missing financial summary with balance calculations"
    fi

    # Transaction validation
    echo ""
    if echo "$content" | grep -q -E "(Transaction_Type.*Credit|Transaction_Type.*Debit)"; then
        echo "✅ TRANSACTION TYPES PROPERLY CATEGORIZED"
    else
        echo "⚠️  Ensure transactions have proper Credit/Debit categorization"
    fi

    # Date format validation
    if echo "$content" | grep -q -E "[0-9]{2}-[0-9]{2}-[0-9]{4}"; then
        echo "✅ DATE FORMAT STANDARDIZED (DD-MM-YYYY)"
    else
        echo "⚠️  Ensure dates follow DD-MM-YYYY format"
    fi

    echo ""
    echo "📊 VALIDATION SUMMARY:"
    echo "   • Use validation_hooks.py for detailed validation"
    echo "   • Follow bank-statement-extractor agent patterns"
    echo "   • Ensure financial calculations are accurate"
    echo ""
}

# Function to provide improvement suggestions
suggest_improvements() {
    echo "💡 IMPROVEMENT SUGGESTIONS:"
    echo ""
    echo "For Standardized Output:"
    echo "   • Import validation_hooks.py in your extractor"
    echo "   • Use @validate_output decorator on extract functions"
    echo "   • Follow the exact JSON schema in the agent specification"
    echo ""
    echo "For Financial Accuracy:"
    echo "   • Validate opening_balance + net_change = closing_balance"
    echo "   • Ensure total_credits - total_debits = net_change"
    echo "   • Cross-verify transaction counts across all sections"
    echo ""
    echo "🔧 Quick fix: Add this to your extractor:"
    echo "   from validation_hooks import validate_output"
    echo "   @validate_output"
    echo "   def extract_bank_statement(...):"
    echo ""
}

# Main hook logic
main() {
    # Read input from stdin if available, otherwise use command line args
    if [ -p /dev/stdin ]; then
        content=$(cat)
    else
        content="$*"
    fi

    # Check if this is bank statement output
    if is_bank_output "$content"; then
        validate_output "$content"
        suggest_improvements

        # Log hook activation
        echo "$(date): Output validation hook triggered" >> ~/.claude/hooks.log
    fi
}

# Execute main function
main "$@"