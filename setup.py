"""
Setup script for chatbot_system package.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="chatbot_system",
    version="1.0.0",
    author="Manyachandra",
    author_email="132090383+Manyachandra@users.noreply.github.com",
    description="Production-ready human-like conversational AI chatbot",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Manyachandra/STAN",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "chatbot_system": ["config/*.yaml"],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "ruff>=0.1.9",
            "mypy>=1.8.0",
        ],
        "monitoring": [
            "prometheus-client>=0.19.0",
            "structlog>=23.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "chatbot-server=chatbot_system.examples.api_server:main",
        ],
    },
    include_package_data=True,
)
