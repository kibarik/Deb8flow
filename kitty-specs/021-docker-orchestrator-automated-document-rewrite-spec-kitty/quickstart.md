# Quickstart: Docker Orchestrator

**Feature**: 021-docker-orchestrator-automated-document-rewrite-spec-kitty
**Version**: 1.0.0

## Overview

The Docker Orchestrator automatically processes text documents through the complete Spec-Kitty workflow (specify → research → plan → tasks → implement → review → accept). It runs as a one-shot CLI tool that manages Docker containers with Claude Code + Spec-Kitty environment.

## Prerequisites

### Required

1. **Docker Engine** (27.0+ recommended)
   - macOS: Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - Linux: Install [Docker Engine](https://docs.docker.com/engine/install/)
   - Windows: Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)

2. **Python 3.12+**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

3. **Poetry** (for dependency management)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

### Verification

```bash
# Check Docker
docker --version
docker ps  # Should not error

# Check Python
python --version

# Check Poetry
poetry --version
```

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-org/Deb8flow.git
cd Deb8flow
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Build Docker Image

The orchestrator requires a Docker image with Claude Code and Spec-Kitty:

```bash
# Build image from Dockerfile
docker build -t claude-code:latest -f docker/Dockerfile .
```

Or pull pre-built image:

```bash
docker pull your-registry/claude-code:latest
docker tag your-registry/claude-code:latest claude-code:latest
```

### 4. Configure API Key

Set your Claude API key in environment or config:

```bash
# Option 1: Environment variable
export CLAUDE_API_KEY="your-api-key-here"

# Option 2: Add to config/debate_config.yaml
echo 'api_key: "your-api-key-here"' >> config/debate_config.yaml
```

### 5. Verify Installation

```bash
poetry run python scripts/orchestrator --help
```

## Basic Usage

### Simple Example

Process a document with corrections:

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md
```

This will:
1. Start Docker container with Claude Code + Spec-Kitty
2. Run full Spec-Kitty workflow automatically
3. Generate corrected output at `docs/spec.corrected.md`
4. Stop container and exit

### With Custom Output

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md \
  --output docs/updated-spec.md
```

### Verbose Mode

See detailed progress:

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md --verbose
```

### Dry Run

Validate without executing:

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md --dry-run
```

## Configuration

### Configuration File

Edit `config/debate_config.yaml`:

```yaml
orchestrator:
  # Workflow control
  max_retries: 3
  validation_timeout: 30
  auto_accept: false

  # Output settings
  output_suffix: ".corrected."
  timestamp_output: false

  # Container management
  docker_image: "claude-code:latest"
  keep_containers: false
  container_timeout: 3600

  # Logging
  log_dir: ".orchestrator/logs"
  log_level: "INFO"
  verbose: false
```

### Custom Config File

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md \
  --config config/custom-config.yaml
```

### Override Options

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md \
  --max-retries 5 \
  --timeout 7200
```

## Understanding the Workflow

The orchestrator runs these phases automatically:

1. **specify**: Create feature specification from source + corrections
2. **research**: Research technical questions
3. **plan**: Generate implementation plan
4. **tasks**: Create work packages
5. **implement**: Execute work packages
6. **review**: Review implementation
7. **accept**: Accept and finalize

Each phase can validate its output and retry if needed.

## Output Files

### Corrected Document

The main output is the corrected document:

```
docs/spec.md          → Original (preserved)
docs/spec.corrected.md → Corrected output
```

### Logs

Detailed logs are written to `.orchestrator/logs/`:

```
.orchestrator/logs/
├── orchestrator-20250221-153000.log    # Main log
├── container-20250221-153000.log       # Container logs
└── agent-20250221-153000.log           # Agent communication
```

### Artifacts

Spec-Kitty artifacts are generated in `kitty-specs/`:

```
kitty-specs/
└── [feature-number]-[feature-name]/
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    └── ...
```

## Troubleshooting

### Docker Not Running

**Error**: `ERROR: Docker daemon is not running`

**Solution**:
```bash
# macOS
open -a Docker

# Linux
sudo systemctl start docker

# Windows
# Start Docker Desktop from Start Menu
```

### Permission Denied

**Error**: `ERROR: Permission denied while trying to connect to Docker daemon`

**Solution**:
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo (not recommended)
sudo poetry run python scripts/orchestrator ...
```

### Container Timeout

**Error**: `Workflow exceeded configured timeout`

**Solution**: Increase timeout in config or CLI:

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md \
  --timeout 7200  # 2 hours
```

### API Key Issues

**Error**: `Claude API key not configured or invalid`

**Solution**:
```bash
# Set environment variable
export CLAUDE_API_KEY="sk-ant-..."

# Or add to config
echo 'api_key: "sk-ant-..."' >> config/debate_config.yaml
```

### Insufficient Disk Space

**Error**: `ERROR: Insufficient disk space for container`

**Solution**:
```bash
# Clean up unused Docker resources
docker system prune -a

# Check available space
df -h
```

## Advanced Usage

### Keep Containers for Debugging

```bash
poetry run python scripts/orchestrator docs/spec.md reviews/changes.md \
  --keep-containers

# Inspect container
docker exec -it claude-orchestrator-xyz bash

# Clean up manually
docker stop claude-orchestrator-xyz
docker rm claude-orchestrator-xyz
```

### Custom Phase Configuration

Disable specific phases in config:

```yaml
orchestrator:
  phases:
    - name: "specify"
      enabled: true
      validate: true
    - name: "research"
      enabled: false  # Skip research
      validate: false
    - name: "plan"
      enabled: true
      validate: true
    # ...
```

### Batching Multiple Documents

Not supported in one-shot mode. Run separately:

```bash
for file in docs/*.md; do
  corrections="reviews/$(basename $file .md)-changes.md"
  poetry run python scripts/orchestrator "$file" "$corrections"
done
```

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | Output file generated |
| 1 | Partial | Some phases failed, check logs |
| 2 | Failed | Workflow failed, check logs |
| 3 | Validation Error | Input files invalid |
| 4 | Docker Error | Docker not available |
| 5 | Timeout | Workflow took too long |
| 130 | Interrupted | User cancelled (Ctrl+C) |

## Getting Help

```bash
# Show help
poetry run python scripts/orchestrator --help

# Show version
poetry run python scripts/orchestrator --version

# Check logs
cat .orchestrator/logs/orchestrator-*.log
```

## Next Steps

- Read [full documentation](../../docs/orchestrator.md)
- Review [configuration options](contracts/config-schema.yaml)
- Understand [agent protocol](contracts/agent-protocol.md)
- Check [CLI interface](contracts/cli-interface.md)
