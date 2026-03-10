#!/bin/bash
# Test wrapper for multi-workspace setup wizard with dummy values

set -euo pipefail

# Dummy values (do NOT use in production)
export DATABRICKS_TOKEN="dapi_dummy_token_value"
export DATABRICKS_CLIENT_SECRET="dummy_client_secret"

echo "Running setup wizard with dummy env vars..."
make setup
