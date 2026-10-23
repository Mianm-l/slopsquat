from setuptools import setup, find_packages

setup(
    name="slopsquat",
    version="0.1.0",
    description="A lightweight scanner against AI Package Hallucination & Slopsquatting supply chain risks.",
    long_description=open("README.md", "r", encoding="utf-8").read() if open("README.md", "r", encoding="utf-8") else "",
    long_description_content_type="text/markdown",
    author="Mianm-l",
    url="https://github.com/Mianm-l/slopsquat",
    packages=find_packages(),
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "slopsquat = slopsquat.cli:main",
        ],
    },
    classifiers=[
        "Topic :: Security",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
