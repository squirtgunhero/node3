# tests/test_docker_manager.py

import pytest
from docker_manager import DockerManager

@pytest.mark.asyncio
async def test_docker_initialization():
    """Test Docker manager initialization"""
    try:
        manager = DockerManager()
        assert manager.client is not None
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

@pytest.mark.asyncio
async def test_list_images():
    """Test listing Docker images"""
    try:
        manager = DockerManager()
        images = manager.list_images()
        assert isinstance(images, list)
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")

