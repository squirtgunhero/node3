# Test Jobs for node3 Agent

This directory contains CPU-only test jobs for verifying the node3 agent job execution pipeline.

## Test Jobs

### 1. Simple CPU Test (`Dockerfile.test-simple`)
- **Purpose**: Basic CPU-only test job
- **Image**: `node3-test-simple:latest`
- **Duration**: ~10 seconds
- **Reward**: 0.0001 SOL

### 2. Math Computation Test (`Dockerfile.test-math`)
- **Purpose**: CPU-intensive mathematical computation (pi approximation)
- **Image**: `node3-test-math:latest`
- **Duration**: ~30 seconds
- **Reward**: 0.0002 SOL

### 3. File Processing Test (`Dockerfile.test-file-process`)
- **Purpose**: File I/O and data processing
- **Image**: `node3-test-file-process:latest`
- **Duration**: ~15 seconds
- **Reward**: 0.00015 SOL

## Building Test Images

### Option 1: Use Build Script
```bash
cd test_jobs
./build_test_images.sh
```

### Option 2: Build Manually
```bash
cd test_jobs

# Build simple test
docker build -f Dockerfile.test-simple -t node3-test-simple:latest .

# Build math test
docker build -f Dockerfile.test-math -t node3-test-math:latest .

# Build file processing test
docker build -f Dockerfile.test-file-process -t node3-test-file-process:latest .
```

## Usage

1. **Build the test images** (see above)

2. **Start the mock marketplace**:
   ```bash
   python mock_marketplace.py
   ```

3. **Start the agent**:
   ```bash
   MARKETPLACE_URL=http://127.0.0.1:8000 python main.py
   ```

4. **Run test script** (optional):
   ```bash
   python test_job_execution.py
   ```

## Test Job Structure

Each test job:
- Runs in a Docker container
- Reads from `/input` directory (if provided)
- Writes results to `/output` directory
- Completes successfully and exits with code 0
- Does NOT require GPU (CPU-only)

## Adding New Test Jobs

1. Create a new Dockerfile (e.g., `Dockerfile.test-myjob`)
2. Create the test script (e.g., `myjob_test.py`)
3. Add job definition to `test_jobs.json`
4. Build the image: `docker build -f Dockerfile.test-myjob -t node3-test-myjob:latest .`

## Troubleshooting

**Docker not available?**
- The agent will still connect to marketplace and show jobs
- Jobs won't execute without Docker
- See `GPU_STATUS.md` for details

**Images not found?**
- Make sure you've built the images using `build_test_images.sh`
- Check with: `docker images | grep node3-test`

**Jobs not appearing?**
- Check `test_jobs.json` exists and is valid JSON
- Verify mock marketplace loaded jobs: `curl http://127.0.0.1:8000/api/status`


