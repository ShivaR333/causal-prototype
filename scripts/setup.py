from setuptools import setup, find_packages

setup(
    name="causal-analysis",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "dowhy>=0.8",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "pydantic>=2.0.0",
        "numpy>=1.24.0",
        "pandas>=2.0.0",
        "scipy>=1.10.0",
        "networkx>=2.8,<3.0",
        "matplotlib>=3.7.0",
        "click>=8.1.0",
        "python-multipart>=0.0.6",
        "pytest>=7.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "causal-analysis=causal_analysis.cli.main:cli",
        ],
    },
)