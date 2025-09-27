#!/bin/bash
# Claude Code Hook: Financial Accuracy Validation
# Validates financial calculations and balance consistency in bank statement outputs

# Hook Configuration
HOOK_NAME="financial-accuracy"

# Function to check if content contains financial data
has_financial_data() {
    local content="$1"

    if echo "$content" | grep -q -E "(balance|credit|debit|amount)" || \
       echo "$content" | grep -q -E "[0-9]+\.[0-9]{2}" || \
       echo "$content" | grep -q -E "(opening_balance|closing_balance|total_credits|total_debits)"; then
        return 0
    fi

    return 1
}

# Function to extract and validate financial numbers
validate_financial_accuracy() {
    local content="$1"

    echo "💰 FINANCIAL ACCURACY HOOK ACTIVATED"
    echo ""

    # Extract key financial indicators
    local opening_balance=$(echo "$content" | grep -o '"opening_balance"[^0-9]*[0-9]*\.[0-9]*' | grep -o '[0-9]*\.[0-9]*$' | head -1)
    local closing_balance=$(echo "$content" | grep -o '"closing_balance"[^0-9]*[0-9]*\.[0-9]*' | grep -o '[0-9]*\.[0-9]*$' | head -1)
    local total_credits=$(echo "$content" | grep -o '"total_credits"[^0-9]*[0-9]*\.[0-9]*' | grep -o '[0-9]*\.[0-9]*$' | head -1)
    local total_debits=$(echo "$content" | grep -o '"total_debits"[^0-9]*[0-9]*\.[0-9]*' | grep -o '[0-9]*\.[0-9]*$' | head -1)
    local net_change=$(echo "$content" | grep -o '"net_change"[^0-9-]*-[0-9]*\.[0-9]*\|"net_change"[^0-9]*[0-9]*\.[0-9]*' | grep -o '-[0-9]*\.[0-9]*$\|[0-9]*\.[0-9]*$' | head -1)

    echo "📊 EXTRACTED FINANCIAL DATA:"
    [ -n "$opening_balance" ] && echo "   Opening Balance: $opening_balance"
    [ -n "$closing_balance" ] && echo "   Closing Balance: $closing_balance"
    [ -n "$total_credits" ] && echo "   Total Credits: $total_credits"
    [ -n "$total_debits" ] && echo "   Total Debits: $total_debits"
    [ -n "$net_change" ] && echo "   Net Change: $net_change"
    echo ""

    # Validation checks
    local validation_passed=true

    # Check 1: Net change calculation
    if [ -n "$total_credits" ] && [ -n "$total_debits" ] && [ -n "$net_change" ]; then
        # Use bc for floating point arithmetic if available
        if command -v bc > /dev/null; then
            local calculated_net=$(echo "$total_credits - $total_debits" | bc -l)
            local diff=$(echo "$calculated_net - $net_change" | bc -l | sed 's/^-//')

            if (( $(echo "$diff > 0.01" | bc -l) )); then
                echo "❌ NET CHANGE CALCULATION ERROR"
                echo "   Expected: $calculated_net, Got: $net_change"
                validation_passed=false
            else
                echo "✅ NET CHANGE CALCULATION VERIFIED"
            fi
        fi
    else
        echo "⚠️  INCOMPLETE FINANCIAL DATA - Cannot verify net change"
        validation_passed=false
    fi

    # Check 2: Balance equation
    if [ -n "$opening_balance" ] && [ -n "$closing_balance" ] && [ -n "$net_change" ]; then
        if command -v bc > /dev/null; then
            local calculated_closing=$(echo "$opening_balance + $net_change" | bc -l)
            local diff=$(echo "$calculated_closing - $closing_balance" | bc -l | sed 's/^-//')

            if (( $(echo "$diff > 0.01" | bc -l) )); then
                echo "❌ BALANCE EQUATION ERROR"
                echo "   Opening ($opening_balance) + Net Change ($net_change) ≠ Closing ($closing_balance)"
                validation_passed=false
            else
                echo "✅ BALANCE EQUATION VERIFIED"
            fi
        fi
    else
        echo "⚠️  INCOMPLETE BALANCE DATA - Cannot verify balance equation"
        validation_passed=false
    fi

    # Check 3: Transaction count consistency
    local total_transactions=$(echo "$content" | grep -o '"total_transactions"[^0-9]*[0-9]*' | grep -o '[0-9]*$' | head -1)
    local transaction_count=$(echo "$content" | grep -o '"transaction_count"[^0-9]*[0-9]*' | grep -o '[0-9]*$' | head -1)

    if [ -n "$total_transactions" ] && [ -n "$transaction_count" ]; then
        if [ "$total_transactions" = "$transaction_count" ]; then
            echo "✅ TRANSACTION COUNT CONSISTENT"
        else
            echo "❌ TRANSACTION COUNT MISMATCH"
            echo "   total_transactions: $total_transactions, transaction_count: $transaction_count"
            validation_passed=false
        fi
    fi

    # Check 4: Currency validation
    if echo "$content" | grep -q '"currency".*"INR"'; then
        echo "✅ CURRENCY STANDARDIZED (INR)"
    else
        echo "⚠️  CURRENCY NOT SPECIFIED OR NON-STANDARD"
    fi

    echo ""
    if [ "$validation_passed" = true ]; then
        echo "🎉 FINANCIAL ACCURACY VALIDATION PASSED"
    else
        echo "❌ FINANCIAL ACCURACY VALIDATION FAILED"
        echo ""
        echo "🔧 RECOMMENDATIONS:"
        echo "   • Use FinancialAccuracyHook.validate_financial_accuracy()"
        echo "   • Implement double-entry validation"
        echo "   • Cross-check calculations with source PDF"
        echo "   • Follow bank-statement-extractor agent patterns"
    fi

    echo ""
}

# Function to provide accuracy improvement tips
suggest_accuracy_improvements() {
    echo "💡 FINANCIAL ACCURACY BEST PRACTICES:"
    echo ""
    echo "1. Mathematical Consistency:"
    echo "   • net_change = total_credits - total_debits"
    echo "   • closing_balance = opening_balance + net_change"
    echo "   • Validate all calculations with ±0.01 tolerance"
    echo ""
    echo "2. Data Integrity:"
    echo "   • Count transactions across all sections"
    echo "   • Verify debit/credit categorization"
    echo "   • Handle multi-page balance calculations"
    echo ""
    echo "3. Implementation:"
    echo "   • Use Decimal for precise currency calculations"
    echo "   • Implement the FinancialAccuracyHook validation"
    echo "   • Add running balance validation where applicable"
    echo ""
    echo "4. Testing:"
    echo "   • Test with multiple statement periods"
    echo "   • Verify against bank's own totals"
    echo "   • Handle edge cases (zero balances, large amounts)"
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

    # Check if this contains financial data
    if has_financial_data "$content"; then
        validate_financial_accuracy "$content"
        suggest_accuracy_improvements

        # Log hook activation
        echo "$(date): Financial accuracy hook triggered" >> ~/.claude/hooks.log
    fi
}

# Execute main function
main "$@"