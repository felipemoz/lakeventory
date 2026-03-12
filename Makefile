.PHONY: help install install-dev install-cli test check \
	inventory inventory-workspace inventory-all inventory-basic inventory-batch inventory-serverless inventory-no-progress \
	inventory-debug inventory-error inventory-verbose \
	inventory-selective inventory-full inventory-incremental \
	inventory-backup inventory-all-backup inventory-all-workspaces \
	inventory-validate \
	setup list-workspaces \
	cache-clear cache-info cache-list \
	build-exe cli-help cli-version \
	docker-build docker-build-all docker-test docker-push \
	publish-test publish

PYTHON ?= python3
WORKSPACE ?=
OUT ?=
OUT_XLSX ?=
OUTPUT_DIR ?=
COLLECTORS ?=
BATCH_SIZE ?=
BATCH_SLEEP_MS ?=
INCLUDE_RUNS ?= 0
INCLUDE_QUERY_HISTORY ?= 0
INCLUDE_DBFS ?= 0
SERVERLESS ?= 0
LOG_LEVEL ?=
BACKUP_WORKSPACE ?= 0
BACKUP_OUT_DIR ?=

help:
	@echo "Available targets:"
	@echo ""
	@echo "Setup:"
	@echo "  make install                # install dependencies"
	@echo "  make install-dev            # install dev dependencies"
	@echo "  make install-cli            # install CLI (pip install -e .)"
	@echo "  make test                   # run tests"
	@echo "  make check                  # health check usando config.yaml"
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
	@echo "  make inventory              # run on default workspace from config.yaml"
	@echo "  make inventory-workspace    # run on specific workspace (WORKSPACE=name)"
	@echo "  make inventory-all          # run on all configured workspaces"
	@echo "  make inventory-basic        # basic run with default options"
	@echo "  make inventory-batch        # run with explicit batching"
	@echo "  make inventory-serverless   # run serverless mode"
	@echo "  make inventory-incremental  # delta mode using cache snapshots"
	@echo "  make inventory-no-progress  # run with progress bars disabled"
	@echo "  make inventory-validate     # validate permissions only (fail on errors)"
	@echo ""
	@echo "Debugging & Logging:"
	@echo "  make inventory-debug        # run with debug logs"
	@echo "  make inventory-error        # show only errors"
	@echo "  make inventory-verbose      # info/verbose logs"
	@echo ""
	@echo "Collectors:"
	@echo "  make inventory-selective    # selected collectors only"
	@echo "  make inventory-full         # heavy collectors enabled"
	@echo "  make inventory-backup       # backup workspace to .dbc + zip"
	@echo "  make inventory-all-backup   # backup all configured workspaces"
	@echo "  make inventory-all-workspaces # alias de inventory-all"
	@echo ""
	@echo "Cache:"
	@echo "  make cache-list             # list cached snapshots"
	@echo "  make cache-info             # show cache snapshot info"
	@echo "  make cache-clear            # clear cache snapshots"
	@echo ""
	@echo "Parameters (optional):"
	@echo "  WORKSPACE=name              # workspace name no config.yaml"
	@echo "  OUTPUT_DIR=path             # override output directory"
	@echo "  OUT=file.md                 # override markdown output file"
	@echo "  OUT_XLSX=file.xlsx          # override Excel output file"
	@echo "  COLLECTORS=list             # comma-separated collectors"
	@echo "  BATCH_SIZE=N                # override items per batch"
	@echo "  BATCH_SLEEP_MS=N            # override sleep ms between batches"
	@echo "  LOG_LEVEL=level             # debug, info, error, warning (default: config.yaml/env/info)"
	@echo "  SERVERLESS=1                # enable serverless mode"
	@echo "  BACKUP_WORKSPACE=1          # enable backup mode"
	@echo "  BACKUP_OUT_DIR=path         # backup output directory"
	@echo ""
	@echo "Examples:"
	@echo "  make setup                                      # configure workspaces"
	@echo "  make inventory-workspace WORKSPACE=dev          # run on dev workspace"
	@echo "  make inventory-all                              # run on all workspaces"
	@echo "  make check WORKSPACE=prod                       # validate specific workspace"
	@echo "  make inventory OUTPUT_DIR=./reports"
	@echo "  make inventory-full OUTPUT_DIR=/tmp/reports BATCH_SIZE=100"
	@echo "  make inventory-selective OUTPUT_DIR=./data COLLECTORS=workspace,jobs"
	@echo "  make inventory-backup BACKUP_OUT_DIR=./backups"

install:
	pip3 install -r requirements.txt

install-dev:
	pip3 install -r requirements.txt
	pip3 install pip-audit

test:
	$(PYTHON) -m pytest -q

check:
	@echo "🔍 Running health check from config.yaml..."
	@echo ""
	$(PYTHON) -m lakeventory.health_check $(if $(WORKSPACE),--workspace $(WORKSPACE),)

inventory:
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(filter 1,$(BACKUP_WORKSPACE)),--backup-workspace,) $(if $(BACKUP_OUT_DIR),--backup-out-dir $(BACKUP_OUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-workspace:
	@if [ -z "$(WORKSPACE)" ]; then echo "WORKSPACE é obrigatório. Ex.: make inventory-workspace WORKSPACE=dev"; exit 1; fi
	$(PYTHON) -m lakeventory --source sdk --workspace $(WORKSPACE) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(BACKUP_OUT_DIR),--backup-out-dir $(BACKUP_OUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-all:
	@echo "Running inventory for all workspaces from config.yaml..."
	$(PYTHON) -m lakeventory --source sdk --all-workspaces $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(BACKUP_OUT_DIR),--backup-out-dir $(BACKUP_OUT_DIR),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-backup:
	@echo "Running workspace backup mode from config.yaml..."
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) --backup-workspace $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(BACKUP_OUT_DIR),--backup-out-dir $(BACKUP_OUT_DIR),)

inventory-all-backup:
	@echo "Running workspace backup mode for all configured workspaces..."
	$(PYTHON) -m lakeventory --all-workspaces --backup-workspace $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(BACKUP_OUT_DIR),--backup-out-dir $(BACKUP_OUT_DIR),)

setup:
	@echo "Running interactive setup wizard..."
	$(PYTHON) -m lakeventory setup

list-workspaces:
	@echo "Configured workspaces:"
	$(PYTHON) -m lakeventory --list-workspaces

inventory-basic:
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-validate:
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) --validate-permissions $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),)

inventory-batch:
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),)

inventory-serverless:
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) --serverless $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),)

inventory-no-progress:
	INVENTORY_PROGRESS=0 $(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-debug:
	$(MAKE) inventory LOG_LEVEL=debug

inventory-error:
	$(MAKE) inventory LOG_LEVEL=error

inventory-verbose:
	$(MAKE) inventory LOG_LEVEL=verbose

inventory-selective:
	@echo "Run specific collectors with COLLECTORS=workspace,jobs,clusters"
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) $(if $(COLLECTORS),--collectors $(COLLECTORS),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),) $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-full:
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),) --include-runs --include-query-history --include-dbfs $(if $(filter 1,$(SERVERLESS)),--serverless,)

inventory-incremental:
	@echo "Running incremental inventory (delta mode - only changes since last run)"
	$(PYTHON) -m lakeventory --source sdk $(if $(WORKSPACE),--workspace $(WORKSPACE),) $(if $(OUT),--out $(OUT),) $(if $(LOG_LEVEL),--log-level $(LOG_LEVEL),) $(if $(OUTPUT_DIR),--out-dir $(OUTPUT_DIR),) $(if $(OUT_XLSX),--out-xlsx $(OUT_XLSX),) $(if $(BATCH_SIZE),--batch-size $(BATCH_SIZE),) $(if $(BATCH_SLEEP_MS),--batch-sleep-ms $(BATCH_SLEEP_MS),) --incremental $(if $(filter 1,$(SERVERLESS)),--serverless,)

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
		-v $(PWD)/.lakeventory:/app/.lakeventory:ro \
		-v $(PWD)/output:/data \
		$(DOCKER_IMAGE):$(DOCKER_TAG) collect --out report.md

docker-run-interactive:
	@echo "Running Docker container (interactive)..."
	docker run --rm -it \
		-v $(PWD)/.lakeventory:/app/.lakeventory:ro \
		-v $(PWD)/output:/data \
		$(DOCKER_IMAGE):$(DOCKER_TAG) sh

docker-push:
	@echo "Pushing to registry..."
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(DOCKER_TAG)
	@echo "✓ Pushed: $(DOCKER_REGISTRY)/$(DOCKER_REPO):$(DOCKER_TAG)"

docker-size:
	@echo "Docker image sizes:"
	@docker images $(DOCKER_IMAGE) --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

inventory-all-workspaces: inventory-all
	@true
