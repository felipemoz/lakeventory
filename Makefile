.PHONY: help install install-dev test \
	inventory inventory-basic inventory-batch inventory-serverless inventory-no-progress \
	inventory-debug inventory-error inventory-verbose \
	inventory-selective inventory-full inventory-incremental \
	cache-clear cache-info

PYTHON ?= python3
OUT ?= report.md
OUT_XLSX ?= report.xlsx
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
	@echo "  make inventory              # default run (respects BATCH_SIZE/BATCH_SLEEP_MS/SERVERLESS)"
	@echo "  make inventory-basic        # basic run with default options"
	@echo "  make inventory-batch        # run with explicit batching"
	@echo "  make inventory-serverless   # run serverless mode"
	@echo "  make inventory-incremental  # delta mode using cache snapshots"
	@echo "  make inventory-no-progress  # run with progress bars disabled"
	@echo "  make inventory-debug        # run with debug logs"
	@echo "  make inventory-error        # show only errors"
	@echo "  make inventory-verbose      # info/verbose logs"
	@echo "  make inventory-selective    # selected collectors only"
	@echo "  make inventory-full         # heavy collectors enabled"
	@echo "  make cache-info             # show cache snapshot info"
	@echo "  make cache-clear            # clear cache snapshots"

install:
	pip3 install -r requirements.txt

install-dev:
	pip3 install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

inventory:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-basic:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-batch:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS)

inventory-serverless:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--serverless \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-no-progress:
	INVENTORY_PROGRESS=0 $(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
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
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--collectors $(COLLECTORS) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-full:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
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
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		--incremental $(if $(filter 1,$(SERVERLESS)),--serverless,)

cache-info:
	$(PYTHON) -c "from databricks_inventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); info = c.get_cache_info(); print(f'Cache dir: {info[\"cache_dir\"]}'); print(f'Snapshots: {info[\"total_snapshots\"]}'); [print(f'  - {s}') for s in info['snapshots']]"

cache-clear:
	@echo "Clearing inventory cache..."
	$(PYTHON) -c "from databricks_inventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); deleted = c.clear_cache(); print(f'Deleted {deleted} snapshot files')"
