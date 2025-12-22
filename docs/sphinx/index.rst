.. EPUB to Audiobook/Video Converter documentation master file

====================================
EPUB Converter Documentation
====================================

Welcome to the comprehensive documentation for the EPUB to Audiobook/Video Converter!

This tool automates the conversion of EPUB files into high-quality audiobooks and videos with subtitles, chapter markers, and customizable settings.

.. image:: https://img.shields.io/badge/python-3.9%2B-blue
   :target: https://www.python.org/downloads/
   :alt: Python 3.9+

.. image:: https://img.shields.io/badge/license-MIT-green
   :alt: License

Quick Links
===========

* :ref:`installation`
* :ref:`quickstart`
* :ref:`api-reference`
* :ref:`configuration`

Features
========

✨ **Core Features**

* 📚 EPUB parsing and text extraction
* 🎤 Multiple TTS engines (Edge-TTS, Pyttsx3, Piper)
* 🎬 Video generation with subtitles
* 🔄 Auto-recovery and error handling
* 📊 Performance profiling
* 🐳 Docker support

🎯 **Advanced Features**

* Batch processing
* Checkpoint management
* Custom pronunciation fixes
* Word censoring
* Multiple quality presets
* Memory optimization
* Queue management

Contents
========

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   configuration
   usage

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/core
   api/features
   api/utils

.. toctree::
   :maxdepth: 2
   :caption: Development

   development/contributing
   development/testing
   development/architecture

.. toctree::
   :maxdepth: 1
   :caption: Additional Resources

   changelog
   faq
   troubleshooting

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Architecture Overview
=====================

The project follows a clean, modular architecture:

.. code-block:: text

   epub_project_manager.py  # Main entry point
   ├── core/                # Core functionality
   │   ├── config.py        # Configuration management
   │   ├── epub_io.py       # EPUB parsing
   │   ├── tts.py           # TTS engine integration
   │   ├── video_pipeline.py # Video rendering
   │   └── ...
   ├── features/            # Advanced features
   │   ├── auto_recovery.py
   │   ├── checkpoint_manager.py
   │   └── ...
   └── tests/               # Test suite

Getting Help
============

* 📖 Read the :ref:`quickstart` guide
* 🐛 Report issues on GitHub
* 💬 Join our community discussions
* 📧 Contact: support@example.com

License
=======

This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgments
===============

Built with:

* `MoviePy <https://zulko.github.io/moviepy/>`_ - Video editing
* `edge-tts <https://github.com/rany2/edge-tts>`_ - Text-to-Speech
* `faster-whisper <https://github.com/guillaumekln/faster-whisper>`_ - Subtitles
* `ebooklib <https://github.com/aerkalov/ebooklib>`_ - EPUB parsing
