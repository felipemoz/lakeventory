# Docker Build Guide

## Available Dockerfiles

### 1. Dockerfile (Default - Multi-stage Alpine)

**Best for:** Production use with scheduled runs  
**Size:** 202 MB (measured)  
**Features:** Shell access, health checks, non-root user, native musl compilation

```bash
docker build -t lakeventory:alpine .
docker run --rm -v $(pwd)/.lakeventory:/app/.lakeventory:ro lakeventory:alpine
```

**Stages:**
- Builder: `python:3.11-slim` (compiles dependencies)
- Runtime: `python:3.11-alpine` (minimal runtime)

---

### 2. Dockerfile.distroless (Ultra-minimal)

**Best for:** Maximum security, minimal attack surface  
**Size:** 157 MB (measured)  
**Features:** No shell, no package manager, distroless base

```bash
docker build -f Dockerfile.distroless -t lakeventory:distroless .
docker run --rm -v $(pwd)/.lakeventory:/app/.lakeventory:ro lakeventory:distroless collect --out report.md
```

**Pros:**
- Smallest image with Python runtime
- No shell = harder to exploit
- Google maintains base image

**Cons:**
- Cannot debug inside container (no shell)
- Cannot use complex entrypoint scripts
- Limited to direct Python commands

---

### 3. Dockerfile.static (PyInstaller Standalone)

**Best for:** Portable executable, cross-environment deployment  
**Size:** 91.6 MB (measured) 🏆 **SMALLEST**  
**Features:** Single binary, minimal alpine edge runtime

```bash
docker build -f Dockerfile.static -t lakeventory:static .
docker run lakeventory:static collect --out report.md
```

**Stages:**
- Builder: Creates standalone executable with PyInstaller
- Runtime: Minimal Alpine with just the binary

**Note:** True `FROM scratch` won't work because Python executables need glibc/libc

---

## Build Comparison

| Dockerfile | Base | Size | Shell | Debug | Security |
|------------|------|------|-------|-------|----------|
| Default (Alpine) | python:3.11-alpine | **202 MB** | ✓ | ✓ | Good |
| Distroless | gcr.io/distroless/python3 | **157 MB** | ✗ | ✗ | Excellent |
| Static | alpine:edge | **91.6 MB** 🏆 | ✓ | ✓ | Good |

**Note:** Static variant uses Alpine edge for better musl libc symbol compatibility with PyInstaller.

---

## Build Commands

### Standard Build (Alpine)
```bash
docker build -t lakeventory:latest .
docker build -t lakeventory:alpine .
```

### Distroless Build
```bash
docker build -f Dockerfile.distroless -t lakeventory:distroless .
```

### Static Binary Build
```bash
docker build -f Dockerfile.static -t lakeventory:static .
```

### Build with BuildKit (faster)
```bash
DOCKER_BUILDKIT=1 docker build -t lakeventory:latest .
```

### Multi-platform Build
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t lakeventory:multiarch .
```

---

## Run Examples

### Default (Scheduled Mode)
```bash
docker run -d \
  -v $(pwd)/.lakeventory:/app/.lakeventory:ro \
  -e SCHEDULE_HOURS=24 \
  -v lakeventory_output:/data \
  -v lakeventory_cache:/app/.cache \
  lakeventory:latest
```

### One-time Run
```bash
docker run --rm \
  -v $(pwd)/.lakeventory:/app/.lakeventory:ro \
  -v $(pwd)/output:/data \
  lakeventory:alpine collect --out report.md --out-xlsx report.xlsx
```

### Distroless (Direct Command)
```bash
docker run --rm \
  -v $(pwd)/.lakeventory:/app/.lakeventory:ro \
  lakeventory:distroless collect --out report.md
```

### Static Binary
```bash
docker run --rm \
  -v $(pwd)/.lakeventory:/app/.lakeventory:ro \
  lakeventory:static version
```

---

## Docker Compose

Works with all variants:

```yaml
services:
  lakeventory:
    image: lakeventory:alpine  # or :distroless, :static
    volumes:
      - ./.lakeventory:/app/.lakeventory:ro  # credentials and config
      - lakeventory_output:/app/output
      - lakeventory_cache:/app/.cache
```

---

## Size Optimization Tips

### 1. Use .dockerignore
```
__pycache__
*.pyc
*.pyo
.git
.pytest_cache
.cache
tests/
docs/
*.md
```

### 2. Multi-stage Build (already implemented)
- Builder stage: Installs everything
- Runtime stage: Copies only what's needed

### 3. Clean pip cache
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

### 4. Remove build artifacts
```dockerfile
RUN find /opt/venv -type d -name "__pycache__" -exec rm -rf {} +
```

### 5. Use alpine instead of slim
- `python:3.11-slim`: ~120 MB base
- `python:3.11-alpine`: ~50 MB base

---

## Security Best Practices

All Dockerfiles implement:

✓ **Non-root user**: Runs as UID 1000 (or nonroot for distroless)  
✓ **No unnecessary packages**: Minimal dependencies only  
✓ **Multi-stage build**: Build tools not in final image  
✓ **Health checks**: Verifies application works  
✓ **Read-only filesystem compatible**: No writes to /app  

---

## Troubleshooting

### Common Issues

**1. ImportError: Error relocating ... makecontext: symbol not found**

**Problem:** Alpine's musl libc missing symbols required by cryptography package (compiled against glibc).

**Solution:** Build both stages with Alpine:
- Change builder FROM to `python:3.11-alpine`  
- Install build deps: `gcc g++ musl-dev libffi-dev openssl-dev cargo rust`
- Force native compilation: `pip install --no-binary cryptography`
- Add runtime libs: `apk add libffi openssl ca-certificates`

**2. PyInstaller: pwritev2: symbol not found**

**Problem:** PyInstaller onefile binary requires newer musl symbols than Alpine 3.19 provides.

**Solution:** Use Alpine edge instead of Alpine 3.19:
- Change runtime FROM to `alpine:edge`  
- Provides newer musl libc with required symbols

**3. ModuleNotFoundError: No module named 'lakeventory'**

**Problem:** Editable install (`pip install -e .`) creates symlinks that break when venv is copied between stages.

**Solution:** Use normal install in builder:
- Change to `pip install .` (without `-e` flag)

**4. Image too large?**
- Use `Dockerfile.distroless` (157 MB) or `Dockerfile.static` (91.6 MB)
- Add more files to `.dockerignore`
- Clean `__pycache__` in builder: `find /opt/venv -name "__pycache__" -exec rm -rf {} +`

**5. Cannot debug inside container?**
- Use standard `Dockerfile` (has shell)
- Avoid `Dockerfile.distroless` for debugging (no shell)

**6. PyInstaller build fails?**
- Check `lakeventory.spec` hidden imports
- Build locally first: `make build-exe`
- Ensure lakeventory.spec not excluded in `.dockerignore`

**7. Permission errors?**
- Ensure volumes are writable by UID 1000
- Or run as root: `docker run --user root ...`

**8. COPY file not found in Dockerfile**
- Check `.dockerignore` patterns (wildcards like `*.spec`)
- Add exceptions: `!lakeventory.spec`
- Use wildcard patterns: `LICENSE*` instead of explicit files

---

## CI/CD Integration

### GitHub Actions
```yaml
- name: Build Docker image
  run: |
    docker build -t ghcr.io/${{ github.repository }}:${{ github.sha }} .
    docker push ghcr.io/${{ github.repository }}:${{ github.sha }}
```

### Multi-stage Caching
```dockerfile
# Cache builder stage
docker build --target builder -t lakeventory:builder .
docker build --cache-from lakeventory:builder -t lakeventory:latest .
```

---

## Recommendations

**For Production:** Use default `Dockerfile` (alpine)
- Good balance of size and functionality
- Shell access for debugging
- Health checks enabled

**For Security-Critical:** Use `Dockerfile.distroless`
- Minimal attack surface
- No shell, no package manager
- Google-maintained base

**For Distribution:** Use `Dockerfile.static`
- Portable single binary
- Smallest possible image
- Works across environments

**For Development:** Use standard `Dockerfile`
- Full Python environment
- Easy debugging
- Mount local code as volume
