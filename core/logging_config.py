"""
Centralized Logging Configuration

Provides structured logging with:
- Rotating file handlers
- Separate log files by component
- Colored console output (optional)
- JSON format support
"""

import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from typing import Optional
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color support for console output"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        
        result = super().format(record)
        
        # Reset levelname for other handlers
        record.levelname = levelname
        
        return result


class JSONFormatter(logging.Formatter):
    """Formatter that outputs logs in JSON format"""
    
    def format(self, record):
        import json
        
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage()
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "text",
    enable_console: bool = True,
    enable_colors: bool = True
):
    """
    Setup centralized logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ('text' or 'json')
        enable_console: Enable console output
        enable_colors: Enable colored console output (only for text format)
    """
    # Create log directories
    log_base = Path("logs")
    log_dirs = {
        'main': log_base / "main",
        'tts': log_base / "tts",
        'video': log_base / "video",
        'errors': log_base / "errors",
        'profiling': log_base / "profiling",
        'recovery': log_base / "recovery"
    }
    
    for log_dir in log_dirs.values():
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Text format
    if log_format == "text":
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        if enable_console:
            if enable_colors:
                console_formatter = ColoredFormatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
            else:
                console_formatter = logging.Formatter(
                    '%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%H:%M:%S'
                )
    else:  # JSON format
        file_formatter = JSONFormatter()
        console_formatter = JSONFormatter()
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Main application log
    main_handler = logging.handlers.RotatingFileHandler(
        log_dirs['main'] / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_handler.setLevel(numeric_level)
    main_handler.setFormatter(file_formatter)
    root_logger.addHandler(main_handler)
    
    # Error-only log
    error_handler = logging.handlers.RotatingFileHandler(
        log_dirs['errors'] / "errors.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Component-specific loggers
    setup_component_logger('core.tts', log_dirs['tts'] / "synthesis.log", numeric_level, file_formatter)
    setup_component_logger('core.video_pipeline', log_dirs['video'] / "rendering.log", numeric_level, file_formatter)
    setup_component_logger('features.auto_recovery', log_dirs['recovery'] / "recovery.log", numeric_level, file_formatter)
    setup_component_logger('core.profiler', log_dirs['profiling'] / "performance.log", numeric_level, file_formatter)
    
    logging.info(f"Logging initialized - Level: {log_level}, Format: {log_format}")


def setup_component_logger(logger_name: str, log_file: Path, level: int, formatter: logging.Formatter):
    """Setup a component-specific logger with its own file handler"""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Don't propagate to root logger to avoid duplicate logs
    logger.propagate = True
    
    # Add rotating file handler
    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience function for quick setup
def init_logging(level: str = "INFO", format: str = "text"):
    """Quick logging initialization with defaults"""
    setup_logging(log_level=level, log_format=format)
