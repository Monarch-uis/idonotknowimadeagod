.. _installation:

Installation
============

This guide will help you install the EPUB to Audiobook/Video Converter on your system.

Requirements
------------

**System Requirements:**

* Python 3.9 or higher
* FFmpeg (for video processing)
* 4GB RAM minimum (8GB recommended)
* 5GB free disk space

**Supported Platforms:**

* ✅ Windows 10/11
* ✅ macOS 10.15+
* ✅ Linux (Ubuntu 20.04+, Debian, Fedora)

Method 1: Standard Installation
--------------------------------

1. **Install Python**

   Download Python 3.9+ from `python.org <https://www.python.org/downloads/>`_

2. **Install FFmpeg**

   .. tabs::

      .. tab:: Windows

         Download from `ffmpeg.org <https://ffmpeg.org/download.html>`_ or use Chocolatey:

         .. code-block:: bash

            choco install ffmpeg

      .. tab:: macOS

         Using Homebrew:

         .. code-block:: bash

            brew install ffmpeg

      .. tab:: Linux

         Ubuntu/Debian:

         .. code-block:: bash

            sudo apt update
            sudo apt install ffmpeg espeak-ng

         Fedora:

         .. code-block:: bash

            sudo dnf install ffmpeg espeak-ng

3. **Clone the Repository**

   .. code-block:: bash

      git clone https://github.com/yourusername/epub-converter.git
      cd epub-converter

4. **Create Virtual Environment**

   .. code-block:: bash

      python -m venv .venv
      
      # Windows
      .venv\\Scripts\\activate
      
      # macOS/Linux
      source .venv/bin/activate

5. **Install Dependencies**

   .. code-block:: bash

      pip install -r requirements.txt

6. **Verify Installation**

   .. code-block:: bash

      python run.py --validate-config

Method 2: Docker Installation
------------------------------

1. **Install Docker**

   Download from `docker.com <https://www.docker.com/get-started>`_

2. **Pull or Build Image**

   .. code-block:: bash

      # Option A: Build locally
      docker build -t epub-converter .

      # Option B: Pull from registry (if available)
      docker pull yourusername/epub-converter

3. **Run Container**

   .. code-block:: bash

      docker-compose up

Method 3: Development Installation
-----------------------------------

For contributors and developers:

.. code-block:: bash

   # Clone repository
   git clone https://github.com/yourusername/epub-converter.git
   cd epub-converter

   # Use Makefile for setup
   make setup

   # This will:
   # 1. Create virtual environment
   # 2. Install all dependencies
   # 3. Install development tools
   # 4. Set up pre-commit hooks

Verification
------------

After installation, verify everything works:

.. code-block:: bash

   # Check Python version
   python --version  # Should be 3.9+

   # Check FFmpeg
   ffmpeg -version

   # Validate configuration
   python run.py --validate-config

   # Run tests
   pytest tests/ -v

Troubleshooting
---------------

**FFmpeg not found:**

.. code-block:: bash

   # Windows: Add FFmpeg to PATH
   set PATH=%PATH%;C:\\path\\to\\ffmpeg\\bin

   # macOS/Linux: Check installation
   which ffmpeg

**Permission errors:**

.. code-block:: bash

   # macOS/Linux: Fix permissions
   chmod +x epub_project_manager.py

**Import errors:**

.. code-block:: bash

   # Reinstall dependencies
   pip install --upgrade -r requirements.txt

Next Steps
----------

* Read the :ref:`quickstart` guide
* Configure your settings in ``config.json``
* Place EPUB files in ``_NEW_EPUBS_HERE/``
* Run your first conversion!
