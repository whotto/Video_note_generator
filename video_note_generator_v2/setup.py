"""
Setup script for video_note_generator
"""
from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# 读取requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text().strip().split('\n')
    requirements = [req for req in requirements if req and not req.startswith('#')]

setup(
    name="video-note-generator",
    version="2.0.0",
    author="玄清",
    author_email="grow8org@gmail.com",
    description="一键将视频转换为优质笔记，支持博客和小红书格式",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/whotto/Video_note_generator",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "vnote=video_note_generator.cli:main",
        ],
    },
)
