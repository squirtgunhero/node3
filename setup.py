# setup.py
from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

setup(
    name="node3-agent",
    version="1.0.0",
    description="node3 Agent - Monetize your GPU compute capacity",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="node3 Team",
    author_email="support@node3.com",
    url="https://github.com/node3/agent",
    packages=find_packages(exclude=["tests", "tests.*"]),
    include_package_data=True,
    package_data={
        "": ["templates/*.html"],
    },
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "node3-agent=main:main_entry",
        ],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    keywords="gpu compute blockchain solana decentralized",
)

