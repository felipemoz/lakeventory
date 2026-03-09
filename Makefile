.PHONY: inventory inventory-full

PYTHON ?= /Users/fmoz/Desktop/pp/.venv/bin/python
OUT ?= databricks_as_is.md
OUT_XLSX ?=
BATCH_SIZE ?= 200
BATCH_SLEEP_MS ?= 0
INCLUDE_RUNS ?= 0
INCLUDE_QUERY_HISTORY ?= 0
INCLUDE_DBFS ?= 0

install:
	pip install -r requirements.txt

inventory:
	$(PYTHON) scripts/inventory_databricks_assets.py \
		--source sdk \
		--out $(OUT) \
		--batch-size $(BATCH_SIZE) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)
		--batch-sleep-ms $(BATCH_SLEEP_MS)

inventory-full:
	$(PYTHON) scripts/inventory_databricks_assets.py \
		--source sdk \
		--out $(OUT) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		$(if $(filter 1,$(INCLUDE_RUNS)),--include-runs,) \
		$(if $(filter 1,$(INCLUDE_QUERY_HISTORY)),--include-query-history,) \
		$(if $(filter 1,$(INCLUDE_DBFS)),--include-dbfs,) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)
