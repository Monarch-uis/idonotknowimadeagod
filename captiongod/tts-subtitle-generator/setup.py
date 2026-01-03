from setuptools import setup, find_packages

setup(
    name="tts-subtitle-generator",
    version="0.1.0",
    author="TTS Subtitle Generator",
    description="Generate accurate SRT subtitles by aligning known text with TTS-generated audio",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    install_requires=[
        "librosa>=0.10.0",
        "pydub>=0.25.0",
        "phonemizer>=3.2.1",
        "dtw-python>=1.3.0",
        "numpy>=1.24.0",
        "tqdm>=4.65.0",
    ],
    entry_points={
        "console_scripts": [
            "tts-subtitles=src.cli:main",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
