.. _configuration:

Configuration
=============

Detailed guide to configuring the EPUB converter.

Configuration File Location
---------------------------

The main configuration file is ``config.json`` in the project root.

Audio Settings
--------------

TTS Configuration
~~~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "audio_settings": {
       "voice": "en-US-GuyNeural",
       "tts_speed_default": "+0%",
       "max_concurrent_tts": 4,
       "retry_attempts": 5,
       "edge_tts_request_delay": 0.8
     }
   }

Video Settings
--------------

Quality Presets
~~~~~~~~~~~~~~~

.. code-block:: json

   {
     "video_settings": {
       "current_quality_preset": "Balanced",
       "quality_presets": {
         "Fast": {
           "height": 480,
           "crf": 30,
           "preset": "ultrafast"
         },
         "Balanced": {
           "height": 720,
           "crf": 23,
           "preset": "medium"
         },
         "High": {
           "height": 1080,
           "crf": 20,
           "preset": "slow"
         }
       }
     }
   }

System Limits
-------------

.. code-block:: json

   {
     "system_limits": {
       "max_batch_size": 50,
       "ram_warning_threshold_mb": 1500,
       "enable_memory_monitoring": true
     }
   }
