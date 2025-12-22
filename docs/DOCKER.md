# Docker Deployment Guide

This guide explains how to run the EPUB to Audiobook/Video converter using Docker for easy deployment across different platforms.

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose 2.0 or later
- At least 4GB of available RAM
- 10GB of free disk space

## Quick Start

### 1. Build the Docker Image

```bash
cd c:\Users\DIBAKAR\desktop\idonotknowimadeagod
docker build -t epub-converter:latest .
```

### 2. Run with Docker Compose

```bash
docker-compose up
```

The container will start in interactive mode, allowing you to select EPUBs and configure settings.

### 3. Stop the Container

Press `Ctrl+C` or run:
```bash
docker-compose down
```

## Volume Mappings

The Docker container uses the following volume mappings:

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./Novels` | `/app/Novels` | Active novel projects and work-in-progress |
| `./_NEW_EPUBS_HERE` | `/app/_NEW_EPUBS_HERE` | Input directory for new EPUB files |
| `./output` | `/app/output` | Generated audiobooks and videos |
| `./config.json` | `/app/config.json` | Configuration file (read-only) |
| `./logs` | `/app/logs` | Application logs |
| `./processing_queue.json` | `/app/processing_queue.json` | Processing queue state |

## Configuration

### Resource Limits

Default resource limits in `docker-compose.yml`:
- **CPU**: 4 cores (limit), 2 cores (reservation)
- **Memory**: 4GB (limit), 2GB (reservation)

Adjust these in `docker-compose.yml` based on your system:

```yaml
deploy:
  resources:
    limits:
      cpus: '8.0'      # Increase for faster processing
      memory: 8G
    reservations:
      cpus: '4.0'
      memory: 4G
```

### Environment Variables

Set environment variables in `docker-compose.yml`:

```yaml
environment:
  - PYTHONUNBUFFERED=1
  - TZ=Asia/Kolkata           # Set your timezone
  - LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR
```

## Usage Examples

### Process a Single EPUB

1. Place your EPUB file in `_NEW_EPUBS_HERE/`
2. Start the container:
   ```bash
   docker-compose up
   ```
3. Follow the interactive prompts
4. Find output in `output/` directory

### Run in Background (Detached Mode)

```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

### Execute Commands Inside Container

```bash
# Open a shell in the running container
docker-compose exec epub-converter /bin/bash

# Run with specific flags
docker-compose exec epub-converter python epub_project_manager.py --profile
```

### One-off Command Execution

```bash
docker-compose run --rm epub-converter python epub_project_manager.py --validate-config
```

## Troubleshooting

### Permission Issues

If you encounter permission errors with volume mounts:

**On Linux/Mac:**
```bash
# Change ownership to match container user (UID 1000)
sudo chown -R 1000:1000 Novels/ output/ logs/
```

**On Windows:**
Ensure Docker Desktop has access to the drive where the project is located (Settings → Resources → File Sharing).

### Container Won't Start

Check logs:
```bash
docker-compose logs
```

Common issues:
- **Port conflicts**: Not applicable (no exposed ports)
- **Memory limits**: Increase in `docker-compose.yml`
- **Missing directories**: Create required directories:
  ```bash
  mkdir -p Novels _NEW_EPUBS_HERE output logs
  ```

### FFmpeg Not Found

The Dockerfile includes FFmpeg installation. If you see FFmpeg errors:

1. Rebuild the image:
   ```bash
   docker-compose build --no-cache
   ```

2. Verify FFmpeg is installed:
   ```bash
   docker-compose run --rm epub-converter ffmpeg -version
   ```

### Piper TTS Models Missing

Ensure `piper/` and `piper_models/` directories exist before building:

```bash
# Verify directories
ls -la piper/ piper_models/
```

If missing, download Piper models and place them in `piper_models/`.

## Advanced Configuration

### Custom Dockerfile

To modify the Docker image:

1. Edit `Dockerfile`
2. Rebuild:
   ```bash
   docker build -t epub-converter:latest .
   ```

### Multi-Container Setup

For batch processing with multiple containers:

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  epub-converter-1:
    extends:
      service: epub-converter
    container_name: epub-converter-1
  
  epub-converter-2:
    extends:
      service: epub-converter
    container_name: epub-converter-2
```

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.yml up
```

## Health Checks

The container includes a health check that runs every 30 seconds:

```bash
# Check container health
docker-compose ps
```

Healthy status indicates the Python environment is working correctly.

## Cleanup

### Remove Containers and Images

```bash
# Stop and remove containers
docker-compose down

# Remove image
docker rmi epub-converter:latest

# Remove all unused Docker resources
docker system prune -a
```

### Clean Temporary Files

```bash
# Inside container
docker-compose exec epub-converter find /app/Novels -type d -name "temp_render_files" -exec rm -rf {} +
```

## Performance Tips

1. **Use SSD storage** for volume mounts
2. **Allocate sufficient RAM** (minimum 4GB, recommended 8GB)
3. **Enable Docker BuildKit** for faster builds:
   ```bash
   export DOCKER_BUILDKIT=1
   docker build -t epub-converter:latest .
   ```
4. **Use bind mounts** instead of volumes for better performance on Windows

## Security Considerations

- Container runs as non-root user (`epubuser`, UID 1000)
- Config file is mounted read-only
- No network ports exposed
- Minimal attack surface with slim base image

## Next Steps

- Review `config.json` for customization options
- Check `logs/` directory for detailed application logs
- See main README for feature documentation
