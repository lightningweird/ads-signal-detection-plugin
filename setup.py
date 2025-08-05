from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="signal-detection-plugin",
    version="1.0.0",
    author="Signal Detection Team",
    description="Modular signal detection plugin for ads-anomaly-detection system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/signal-detection-plugin",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "asyncio>=3.4.3",
        "pyyaml>=6.0.2",
        "structlog>=25.4.0",
        "numpy>=2.3.2",
        "scipy>=1.16.1",
        "pandas>=2.3.1",
        "redis>=6.3.0",
        "aioredis>=2.0.1",
        "fastapi>=0.116.1",
        "uvicorn>=0.35.0", 
        "prometheus-client>=0.22.1",
        "aiohttp>=3.9.1",
        "websockets>=15.0.1",
        "msgpack>=1.0.7",
        "python-dotenv>=1.1.1",
        "psutil>=7.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
        ],
        "ml": [
            "scikit-learn>=1.3.2",
            "torch>=2.1.1",
        ],
        "gpu": [
            "cupy-cuda11x>=12.0.0",
            "torch>=2.1.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "signal-detector=src.main:main",
        ],
        "anomaly_detectors": [
            "statistical=src.detectors.statistical:StatisticalAnomalyDetector",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.toml"],
    },
)