.PHONY: help install install-dev test check \
	inventory inventory-basic inventory-batch inventory-serverless inventory-no-progress \
	inventory-debug inventory-error inventory-verbose \
	inventory-selective inventory-full inventory-incremental \
	inventory-validate \
	cache-clear cache-info

PYTHON ?= python3
OUT ?= report.md
OUT_XLSX ?= report.xlsx
OUTPUT_DIR ?= ./.reports
COLLECTORS ?= jobs,clusters,sql,mlflow,unity_catalog,repos,security,identities,serving,sharing,dbfs
BATCH_SIZE ?= 200
BATCH_SLEEP_MS ?= 0
INCLUDE_RUNS ?= 0
INCLUDE_QUERY_HISTORY ?= 0
INCLUDE_DBFS ?= 0
SERVERLESS ?= 0
LOG_LEVEL ?= info

help:
	@echo "Available targets:"
	@echo "  make check                  # health check (dependencies, auth, workspace)"
	@echo "  make inventory              # default run (respects BATCH_SIZE/BATCH_SLEEP_MS/SERVERLESS)"
	@echo "  make inventory-basic        # basic run with default options"
	@echo "  make inventory-batch        # run with explicit batching"
	@echo "  make inventory-serverless   # run serverless mode"
	@echo "  make inventory-incremental  # delta mode using cache snapshots"
	@echo "  make inventory-no-progress  # run with progress bars disabled"
	@echo "  make inventory-validate     # validate permissions only (fail on errors)"
	@echo "  make inventory-debug        # run with debug logs"
	@echo "  make inventory-error        # show only errors"
	@echo "  make inventory-verbose      # info/verbose logs"
	@echo "  make inventory-selective    # selected collectors only"
	@echo "  make inventory-full         # heavy collectors enabled"
	@echo "  make cache-info             # show cache snapshot info"
	@echo "  make cache-clear            # clear cache snapshots"
	@echo ""
	@echo "Parameters (optional):"
	@echo "  OUTPUT_DIR=path             # output directory (default: ./output or from .env)"
	@echo "  OUT=file.md                 # output markdown file (default: report.md)"
	@echo "  OUT_XLSX=file.xlsx          # output Excel file"
	@echo "  COLLECTORS=list             # comma-separated collectors"
	@echo "  BATCH_SIZE=N                # items per batch (default: 200)"
	@echo "  BATCH_SLEEP_MS=N            # sleep ms between batches"
	@echo "  LOG_LEVEL=level             # debug, info, error, warning (default: info)"
	@echo "  SERVERLESS=1                # enable serverless mode"
	@echo ""
	@echo "Examples:"
	@echo "  make inventory OUTPUT_DIR=./reports"
	@echo "  make inventory-full OUTPUT_DIR=/tmp/reports BATCH_SIZE=100"
	@echo "  make inventory-selective OUTPUT_DIR=./data COLLECTORS=workspace,jobs"

install:
	pip3 install -r requirements.txt

install-dev:
	pip3 install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

check:
	@echo "🔍 Running health check..."
	@echo ""
	$(PYTHON) -m databricks_inventory.health_check

inventory:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-basic:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-validate:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--validate-permissions \
		--log-level $(LOG_LEVEL)

inventory-batch:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS)

inventory-serverless:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--serverless \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-no-progress:
	INVENTORY_PROGRESS=0 $(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-debug:
	$(MAKE) inventory LOG_LEVEL=debug

inventory-error:
	$(MAKE) inventory LOG_LEVEL=error

inventory-verbose:
	$(MAKE) inventory LOG_LEVEL=verbose

inventory-selective:
	@echo "Run specific collectors with COLLECTORS=workspace,jobs,clusters"
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--collectors $(COLLECTORS) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-full:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		--include-runs \
		--include-query-history \
		--include-dbfs $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-incremental:
	@echo "Running incremental inventory (delta mode - only changes since last run)"
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		--incremental $(if $(filter 1,$(SERVERLESS)),--serverless,)

cache-info:
	$(PYTHON) -c "from databricks_inventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); info = c.get_cache_info(); print(f'Cache dir: {info[\"cache_dir\"]}'); print(f'Snapshots: {info[\"total_snapshots\"]}'); [print(f'  - {s}') for s in info['snapshots']]"

cache-clear:
	@echo "Clearing inventory cache..."
	$(PYTHON) -c "from databricks_inventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); deleted = c.clear_cache(); print(f'Deleted {deleted} snapshot files')"
