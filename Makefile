.PHONY: help install install-dev install-cli test check \
	inventory inventory-basic inventory-batch inventory-serverless inventory-no-progress \
	inventory-debug inventory-error inventory-verbose \
	inventory-selective inventory-full inventory-incremental \
	inventory-all-workspaces \
	inventory-validate \
	cache-clear cache-info cache-list \
	build-exe cli-help cli-version \
	docker-build docker-build-all docker-test docker-push \
	publish-test publish

PYTHON ?= python3
OUT ?= report.md
OUT_XLSX ?= report.xlsx
OUTPUT_DIR ?= ./.reports
WORKSPACES_CONFIG ?= workspaces.yaml
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
	@echo ""
	@echo "Setup:"
	@echo "  make install                # install dependencies"
	@echo "  make install-dev            # install dev dependencies"
	@echo "  make install-cli            # install CLI (pip install -e .)"
	@echo "  make test                   # run tests"
	@echo "  make check                  # health check (dependencies, auth, workspace)"
	@echo ""
	@echo "CLI Commands (new):"
	@echo "  make cli-help               # show CLI help"
	@echo "  make cli-version            # show version"
	@echo "  make build-exe              # build standalone executable"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build           # build default alpine image"
	@echo "  make docker-build-all       # build all variants (alpine, distroless, static)"
	@echo "  make docker-test            # test docker image"
	@echo "  make docker-push            # push to registry"
	@echo ""
	@echo "Inventory:"
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
	@echo "  make inventory-all-workspaces   # run inventory across all configured workspaces"
	@echo ""
	@echo "Cache:"
	@echo "  make cache-list             # list cached snapshots"
	@echo "  make cache-info             # show cache snapshot info"
	@echo "  make cache-clear            # clear cache snapshots"
	@echo ""
	@echo "Parameters (optional):"
	@echo "  OUTPUT_DIR=path             # output directory (default: ./output or from .env)"
	@echo "  OUT=file.md                 # output markdown file (default: report.md)"
	@echo "  OUT_XLSX=file.xlsx          # output Excel file"
	@echo "  COLLECTORS=list             # comma-separated collectors"
	@echo "  WORKSPACES_CONFIG=path      # workspaces YAML config (default: workspaces.yaml)"
	@echo "  BATCH_SIZE=N                # items per batch (default: 200)"
	@echo "  BATCH_SLEEP_MS=N            # sleep ms between batches"
	@echo "  LOG_LEVEL=level             # debug, info, error, warning (default: info)"
	@echo "  SERVERLESS=1                # enable serverless mode"
	@echo ""
	@echo "Examples:"
	@echo "  make inventory OUTPUT_DIR=./reports"
	@echo "  make inventory-full OUTPUT_DIR=/tmp/reports BATCH_SIZE=100"
	@echo "  make inventory-selective OUTPUT_DIR=./data COLLECTORS=workspace,jobs"
	@echo "  make inventory-all-workspaces WORKSPACES_CONFIG=workspaces.yaml"

install:
	pip3 install -r requirements.txt

install-dev:
	pip3 install -r requirements.txt
	pip3 install pip-audit

test:
	$(PYTHON) -m pytest -q

check:
	@echo "🔍 Running health check..."
	@echo ""
	$(PYTHON) -m lakeventory.health_check

inventory:
	$(PYTHON) -m lakeventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-basic:
	$(PYTHON) -m lakeventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-validate:
	$(PYTHON) -m lakeventory \
		--source sdk \
		--validate-permissions \
		--log-level $(LOG_LEVEL)

inventory-batch:
	$(PYTHON) -m lakeventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS)

inventory-serverless:
	$(PYTHON) -m lakeventory \
		--source sdk \
		--serverless \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-no-progress:
	INVENTORY_PROGRESS=0 $(PYTHON) -m lakeventory \
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
	$(PYTHON) -m lakeventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--collectors $(COLLECTORS) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-full:
	$(PYTHON) -m lakeventory \
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
	$(PYTHON) -m lakeventory \
		--source sdk \
		--out $(OUT) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) \
		--batch-size $(BATCH_SIZE) \
		--batch-sleep-ms $(BATCH_SLEEP_MS) \
		--incremental $(if $(filter 1,$(SERVERLESS)),--serverless,)

cache-info:
	$(PYTHON) -c "from lakeventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); info = c.get_cache_info(); print(f'Cache dir: {info[\"cache_dir\"]}'); print(f'Snapshots: {info[\"total_snapshots\"]}'); [print(f'  - {s}') for s in info['snapshots']]"

cache-list:
	@echo "Listing cached snapshots..."
	@lakeventory cache list 2>/dev/null || $(PYTHON) -m lakeventory.cli cache list

cache-clear:
	@echo "Clearing inventory cache..."
	$(PYTHON) -c "from lakeventory.cache import InventoryCache; from pathlib import Path; c = InventoryCache(); deleted = c.clear_cache(); print(f'Deleted {deleted} snapshot files')"

install-cli:
	@echo "Installing Lakeventory CLI..."
	pip install -e .
	@echo ""
	@echo "✓ CLI installed! Try:"
	@echo "  lakeventory --version"
	@echo "  lakeventory collect --help"

cli-help:
	@lakeventory --help 2>/dev/null || $(PYTHON) -m lakeventory.cli --help

cli-version:
	@lakeventory version 2>/dev/null || $(PYTHON) -m lakeventory.cli version

build-exe:
	@echo "Building standalone executable..."
	@bash scripts/build_executable.sh

publish-test:
	@echo "Publishing to TestPyPI..."
	$(PYTHON) -m build
	$(PYTHON) -m twine upload --repository testpypi dist/*

publish:
	@echo "Publishing to PyPI..."
	$(PYTHON) -m build
	$(PYTHON) -m twine upload dist/*

# Docker targets
DOCKER_IMAGE ?= lakeventory
DOCKER_TAG ?= latest
DOCKER_REGISTRY ?= ghcr.io
DOCKER_REPO ?= felipemoz/lakeventory

docker-build:
	@echo "Building Docker image (alpine multi-stage)..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	docker build -t $(DOCKER_IMAGE):alpine .
	@echo ""
	@echo "✓ Built: $(DOCKER_IMAGE):$(DOCKER_TAG)"
	@docker images $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-build-distroless:
	@echo "Building Docker image (distroless)..."
	docker build -f Dockerfile.distroless -t $(DOCKER_IMAGE):distroless .
	@echo ""
	@echo "✓ Built: $(DOCKER_IMAGE):distroless"
	@docker images $(DOCKER_IMAGE):distroless

docker-build-static:
	@echo "Building Docker image (static binary)..."
	docker build -f Dockerfile.static -t $(DOCKER_IMAGE):static .
	@echo ""
	@echo "✓ Built: $(DOCKER_IMAGE):static"
	@docker images $(DOCKER_IMAGE):static

docker-build-all: docker-build docker-build-distroless docker-build-static
	@echo ""
	@echo "All Docker images built:"
	@docker images $(DOCKER_IMAGE)

docker-test:
	@echo "Testing Docker image..."
	docker run --rm $(DOCKER_IMAGE):$(DOCKER_TAG) python -c "import lakeventory; print(f'Lakeventory {lakeventory.__version__}')"
	@echo "✓ Docker image works!"

docker-run:
	@echo "Running Docker container (one-time inventory)..."
	docker run --rm \
		-e DATABRICKS_HOST \
		-e DATABRICKS_TOKEN \
		-v $(PWD)/output:/app/output \
		$(DOCKER_IMAGE):$(DOCKER_TAG) collect --out report.md

docker-run-interactive:
	@echo "Running Docker container (interactive)..."
	docker run --rm -it \
		-e DATABRICKS_HOST \
		-e DATABRICKS_TOKEN \
		-v $(PWD)/output:/app/output \
		$(DOCKER_IMAGE):$(DOCKER_TAG) sh

docker-push:
	@echo "Pushing to registry..."
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(DOCKER_TAG)
	@echo "✓ Pushed: $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(DOCKER_TAG)"

docker-size:
	@echo "Docker image sizes:"
	@docker images $(DOCKER_IMAGE) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

inventory-all-workspaces:
	@echo "Running inventory across all configured workspaces ($(WORKSPACES_CONFIG))..."
	$(PYTHON) -m lakeventory.multi_workspace_cli \
		--config $(WORKSPACES_CONFIG) \
		--log-level $(LOG_LEVEL) \
		$(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) \
		$(if $(COMPARISON_OUT),--comparison-out $(COMPARISON_OUT),)
