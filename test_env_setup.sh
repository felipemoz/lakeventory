#!/bin/bash

# Create a temporary directory for testing
TEST_DIR=$(mktemp -d)
echo "📁 Test directory: $TEST_DIR"

# Create a .env file with OUTPUT_DIR
cat > "$TEST_DIR/.env" << 'ENVEOF'
OUTPUT_DIR=/tmp/my-reports
ENVEOF

echo "✅ Created .env with OUTPUT_DIR=/tmp/my-reports"
cat "$TEST_DIR/.env"

# Test load_output_dir
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/Users/fmoz/Desktop/pp/inventory')
from pathlib import Path
from databricks_inventory.client import load_output_dir

test_dir = Path(sys.argv[1])
result = load_output_dir(test_dir)
print(f"✅ load_output_dir result: {result}")
PYEOF "$TEST_DIR"

# Cleanup
rm -rf "$TEST_DIR"
echo "✅ Test complete!"
