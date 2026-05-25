from setuptools import setup, find_packages

setup(
    name="digital-humanities-narrative",
    version="0.1.0",
    description="数字人文叙事分析 - 从零散资料重构故事世界",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "spacy>=3.7",
        "transformers>=4.36",
        "torch>=2.1",
        "networkx>=3.2",
        "matplotlib>=3.8",
        "pyvis>=0.3",
        "python-dateutil>=2.8",
        "jieba>=0.42",
        "textblob>=0.17",
        "numpy>=1.24",
        "pandas>=2.0",
    ],
)
