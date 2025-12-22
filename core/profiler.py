"""
Performance Profiler for EPUB to Audiobook/Video Converter

Provides comprehensive profiling capabilities including:
- Function execution timing
- Memory usage tracking
- CPU utilization monitoring
- HTML and JSON report generation
"""

import time
import functools
import cProfile
import pstats
import io
import json
import psutil
import tracemalloc
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Callable, Optional
from contextlib import contextmanager


class PerformanceProfiler:
    """Main profiler class for tracking performance metrics"""
    
    def __init__(self, name: str = "default", output_dir: Path = None):
        """
        Initialize the profiler
        
        Args:
            name: Name for this profiling session
            output_dir: Directory to save profiling reports (default: logs/profiling)
        """
        self.name = name
        self.output_dir = output_dir or Path("logs/profiling")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.metrics: List[Dict[str, Any]] = []
        self.start_time = None
        self.profiler = None
        self.process = psutil.Process()
        
    def start(self):
        """Start profiling"""
        self.start_time = time.time()
        tracemalloc.start()
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        
    def stop(self):
        """Stop profiling"""
        if self.profiler:
            self.profiler.disable()
        tracemalloc.stop()
        
    @contextmanager
    def profile_section(self, section_name: str):
        """
        Context manager for profiling a code section
        
        Usage:
            with profiler.profile_section("EPUB Parsing"):
                parse_epub(file)
        """
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        tracemalloc_snapshot = tracemalloc.take_snapshot()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self.process.memory_info().rss / 1024 / 1024  # MB
            
            # Calculate memory delta
            current_snapshot = tracemalloc.take_snapshot()
            top_stats = current_snapshot.compare_to(tracemalloc_snapshot, 'lineno')
            memory_delta = sum(stat.size_diff for stat in top_stats) / 1024 / 1024  # MB
            
            self.metrics.append({
                'section': section_name,
                'duration_seconds': end_time - start_time,
                'memory_start_mb': start_memory,
                'memory_end_mb': end_memory,
                'memory_delta_mb': memory_delta,
                'timestamp': datetime.now().isoformat()
            })
    
    def generate_report(self, format: str = "html") -> Path:
        """
        Generate profiling report
        
        Args:
            format: Report format ('html' or 'json')
            
        Returns:
            Path to generated report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            return self._generate_json_report(timestamp)
        else:
            return self._generate_html_report(timestamp)
    
    def _generate_json_report(self, timestamp: str) -> Path:
        """Generate JSON profiling report"""
        report_path = self.output_dir / f"profile_{self.name}_{timestamp}.json"
        
        # Get cProfile stats
        stats_io = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=stats_io)
        stats.sort_stats('cumulative')
        stats.print_stats(50)  # Top 50 functions
        
        report_data = {
            'session_name': self.name,
            'timestamp': timestamp,
            'total_duration': time.time() - self.start_time if self.start_time else 0,
            'sections': self.metrics,
            'top_functions': stats_io.getvalue()
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_path
    
    def _generate_html_report(self, timestamp: str) -> Path:
        """Generate HTML profiling report"""
        report_path = self.output_dir / f"profile_{self.name}_{timestamp}.html"
        
        # Calculate total metrics
        total_duration = sum(m['duration_seconds'] for m in self.metrics)
        max_memory = max((m['memory_end_mb'] for m in self.metrics), default=0)
        
        # Get cProfile stats
        stats_io = io.StringIO()
        stats = pstats.Stats(self.profiler, stream=stats_io)
        stats.sort_stats('cumulative')
        stats.print_stats(50)
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Profile: {self.name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }}
        .metric-card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; }}
        .metric-card .value {{ font-size: 24px; font-weight: bold; color: #333; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #4CAF50; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        tr:hover {{ background: #f5f5f5; }}
        .duration {{ color: #2196F3; font-weight: bold; }}
        .memory {{ color: #FF9800; font-weight: bold; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
        .timestamp {{ color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Performance Profile: {self.name}</h1>
        <p class="timestamp">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <div class="summary">
            <div class="metric-card">
                <h3>Total Duration</h3>
                <div class="value">{total_duration:.2f}s</div>
            </div>
            <div class="metric-card">
                <h3>Peak Memory</h3>
                <div class="value">{max_memory:.1f} MB</div>
            </div>
            <div class="metric-card">
                <h3>Sections Profiled</h3>
                <div class="value">{len(self.metrics)}</div>
            </div>
        </div>
        
        <h2>Section Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Section</th>
                    <th>Duration</th>
                    <th>Memory Start</th>
                    <th>Memory End</th>
                    <th>Memory Delta</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for metric in self.metrics:
            html_content += f"""
                <tr>
                    <td>{metric['section']}</td>
                    <td class="duration">{metric['duration_seconds']:.3f}s</td>
                    <td class="memory">{metric['memory_start_mb']:.1f} MB</td>
                    <td class="memory">{metric['memory_end_mb']:.1f} MB</td>
                    <td class="memory">{metric['memory_delta_mb']:+.1f} MB</td>
                </tr>
"""
        
        html_content += f"""
            </tbody>
        </table>
        
        <h2>Top 50 Functions by Cumulative Time</h2>
        <pre>{stats_io.getvalue()}</pre>
    </div>
</body>
</html>
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_path


def profile_function(section_name: Optional[str] = None):
    """
    Decorator for profiling individual functions
    
    Usage:
        @profile_function("TTS Synthesis")
        def synthesize_speech(text):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if profiling is enabled globally
            if not hasattr(wrapper, '_profiler_enabled'):
                return func(*args, **kwargs)
            
            profiler = getattr(wrapper, '_profiler_instance', None)
            if not profiler:
                return func(*args, **kwargs)
            
            name = section_name or func.__name__
            with profiler.profile_section(name):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Global profiler instance
_global_profiler: Optional[PerformanceProfiler] = None


def enable_profiling(name: str = "global", output_dir: Path = None):
    """Enable global profiling"""
    global _global_profiler
    _global_profiler = PerformanceProfiler(name, output_dir)
    _global_profiler.start()
    return _global_profiler


def disable_profiling(generate_report: bool = True, format: str = "html") -> Optional[Path]:
    """Disable global profiling and optionally generate report"""
    global _global_profiler
    if _global_profiler:
        _global_profiler.stop()
        if generate_report:
            report_path = _global_profiler.generate_report(format)
            _global_profiler = None
            return report_path
        _global_profiler = None
    return None


def get_profiler() -> Optional[PerformanceProfiler]:
    """Get the global profiler instance"""
    return _global_profiler
