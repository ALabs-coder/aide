#!/bin/bash
# Claude Code Hook: Bank Statement Extractor Trigger
# Automatically triggers bank-statement-extractor agent for PDF processing tasks

# Hook Configuration
HOOK_NAME="bank-extractor-trigger"
AGENT_FILE="/Users/ramanjaneyulumedikonda/dev/aide/.claude/agents/bank-statement-extractor.md"

# Function to check if task involves bank statement extraction
is_bank_extraction_task() {
    local input="$1"

    # Check for bank extraction keywords
    if echo "$input" | grep -iq -E "(bank statement|pdf extract|transaction extract|canara bank|union bank|statement processing|bank.*pdf)" || \
       echo "$input" | grep -iq -E "(api/extractors|extract_pdf_data|bank.*statement|pdf.*data)" || \
       echo "$input" | grep -q -E "\.(pdf|PDF)" || \
       echo "$input" | grep -iq "extractor"; then
        return 0
    fi

    return 1
}

# Function to suggest using bank extractor agent
suggest_bank_extractor() {
    echo "🏦 BANK EXTRACTOR HOOK ACTIVATED"
    echo ""
    echo "This task appears to involve bank statement extraction. Consider using the bank-statement-extractor agent:"
    echo ""
    echo "💡 Suggested approach:"
    echo "   • Use the bank-statement-extractor agent for optimal results"
    echo "   • Agent specializes in: Canara Bank, Union Bank extractors"
    echo "   • Enforces standardized JSON output schema"
    echo "   • Includes financial accuracy validation"
    echo "   • Follows your CLAUDE.md rules automatically"
    echo ""
    echo "🎯 Agent benefits:"
    echo "   ✓ Standardized Output: Consistent JSON structure"
    echo "   ✓ Financial Accuracy: Built-in balance validation"
    echo "   ✓ Error Handling: Comprehensive PDF processing"
    echo "   ✓ Lambda Architecture: Optimized for your serverless setup"
    echo ""
}

# Main hook logic
main() {
    # Read input from stdin if available, otherwise use command line args
    if [ -p /dev/stdin ]; then
        input=$(cat)
    else
        input="$*"
    fi

    # Check if this is a bank extraction task
    if is_bank_extraction_task "$input"; then
        suggest_bank_extractor

        # Log hook activation
        echo "$(date): Bank extractor hook triggered for: ${input:0:50}..." >> ~/.claude/hooks.log
    fi
}

# Execute main function
main "$@"