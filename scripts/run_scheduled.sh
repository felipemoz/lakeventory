#!/bin/sh
set -e

interval_minutes=${RUN_INTERVAL_MINUTES:-1440}
output_dir=${OUTPUT_DIR:-/app/output}
out_file=${OUT:-report.md}
log_level=${LOG_LEVEL:-info}
batch_size=${BATCH_SIZE:-200}
batch_sleep_ms=${BATCH_SLEEP_MS:-0}
cache_dir=${CACHE_DIR:-/app/.inventory_cache}
incremental_after_first=${INCREMENTAL_AFTER_FIRST:-1}
force_full=${FORCE_FULL:-0}

args="--source sdk --out ${out_file} --log-level ${log_level} --batch-size ${batch_size} --batch-sleep-ms ${batch_sleep_ms}"

if [ -n "${OUTPUT_DIR}" ]; then
  args="$args --out-dir ${output_dir}"
fi

if [ -n "${OUT_XLSX}" ]; then
  args="$args --out-xlsx ${OUT_XLSX}"
fi

if [ -n "${cache_dir}" ]; then
  args="$args --cache-dir ${cache_dir}"
fi

if [ "${SERVERLESS}" = "1" ]; then
  args="$args --serverless"
fi

if [ -n "${COLLECTORS}" ]; then
  args="$args --collectors ${COLLECTORS}"
fi

if [ "${INCLUDE_RUNS}" = "1" ]; then
  args="$args --include-runs"
fi

if [ "${INCLUDE_QUERY_HISTORY}" = "1" ]; then
  args="$args --include-query-history"
fi

if [ "${INCLUDE_DBFS}" = "1" ]; then
  args="$args --include-dbfs"
fi

mkdir -p "${output_dir}"
mkdir -p "${cache_dir}"

while true; do
  run_mode=""
  if [ "${force_full}" = "1" ]; then
    run_mode=""
  elif [ "${incremental_after_first}" = "1" ] && ls "${cache_dir}"/snapshot_*.json >/dev/null 2>&1; then
    run_mode="--incremental"
  fi

  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Running Lakeventory..."
  python -m lakeventory $args $run_mode
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Done. Sleeping ${interval_minutes} minutes..."
  sleep $((interval_minutes * 60))
done
