FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY lakeventory ./lakeventory
COPY docs ./docs
COPY README.md LICENSE CONTRIBUTORS.md Makefile ./
COPY scripts/run_scheduled.sh /app/run_scheduled.sh

RUN chmod +x /app/run_scheduled.sh

ENTRYPOINT ["/app/run_scheduled.sh"]
