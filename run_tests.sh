#!/bin/bash
# Run all unit tests for the PDF Toolbox project

echo "======================================"
echo "Running PDF Toolbox Unit Tests"
echo "======================================"
echo ""

# Set PYTHONPATH to project root
export PYTHONPATH=.

echo "Testing Domain Layer..."
python -m unittest discover tests/unit/domain -v
DOMAIN_RESULT=$?
echo ""

echo "Testing Infrastructure Layer..."
python -m unittest discover tests/unit/infrastructure -v
INFRA_RESULT=$?
echo ""

echo "Testing Application Layer..."
python -m unittest discover tests/unit/application -v
APP_RESULT=$?
echo ""

echo "Testing Presentation Layer..."
python -m unittest discover tests/unit/presentation -v
PRES_RESULT=$?
echo ""

echo "======================================"
echo "Test Summary"
echo "======================================"
echo "Domain Layer:         $([ $DOMAIN_RESULT -eq 0 ] && echo '✓ PASSED' || echo '✗ FAILED')"
echo "Infrastructure Layer: $([ $INFRA_RESULT -eq 0 ] && echo '✓ PASSED' || echo '✗ FAILED')"
echo "Application Layer:    $([ $APP_RESULT -eq 0 ] && echo '✓ PASSED' || echo '✗ FAILED')"
echo "Presentation Layer:   $([ $PRES_RESULT -eq 0 ] && echo '✓ PASSED' || echo '✗ FAILED')"
echo "======================================"

# Exit with error if any test failed
if [ $DOMAIN_RESULT -ne 0 ] || [ $INFRA_RESULT -ne 0 ] || [ $APP_RESULT -ne 0 ] || [ $PRES_RESULT -ne 0 ]; then
    echo "Some tests failed!"
    exit 1
else
    echo "All tests passed! ✓"
    exit 0
fi
