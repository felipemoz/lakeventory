.PHONY: inventory inventory-full inventory-selective inventory-incremental install install-dev test cache-clear cache-info

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

install:
	pip3 install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

inventory:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--batch-size $(BATCH_SIZE) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		$(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-selective:
	@echo "Run specific collectors with COLLECTORS=workspace,jobs,clusters"
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--collectors $(COLLECTORS) \
		--batch-size $(BATCH_SIZE) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		$(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-full:
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		--include-runs \
		--include-query-history \
		--include-dbfs \ \
		$(if $(filter 1,$(SERVERLESS)),--serverless,)
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-incremental:
	@echo "Running incremental inventory (delta mode - only changes since last run)"
	$(PYTHON) -m databricks_inventory \
		--source sdk \
		--out $(OUT) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		--incremental \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		$(if $(filter 1,$(SERVERLESS)),--serverless,)

cache-info:
	$(PYTHON) -c "from databricks_inventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); info = c.get_cache_info(); print(f'Cache dir: {info[\"cache_dir\"]}'); print(f'Snapshots: {info[\"total_snapshots\"]}'); [print(f'  - {s}') for s in info['snapshots']]"

cache-clear:
	@echo "Clearing inventory cache..."
	$(PYTHON) -c "from databricks_inventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); deleted = c.clear_cache(); print(f'Deleted {deleted} snapshot files')"
