"""
Performance Benchmark Suite
Tracks processing speed, memory usage, and generates performance reports
"""
import os
import sys
import time
import json
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class BenchmarkResult:
    """Single benchmark result"""
    test_name: str
    duration_seconds: float
    memory_peak_mb: float
    memory_average_mb: float
    cpu_percent: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class BenchmarkSummary:
    """Summary of all benchmarks"""
    total_tests: int
    successful_tests: int
    failed_tests: int
    total_duration: float
    average_duration: float
    peak_memory_mb: float
    average_memory_mb: float
    average_cpu_percent: float
    timestamp: str
    results: List[Dict[str, Any]]


class PerformanceBenchmark:
    """
    Performance benchmarking system
    
    Features:
    - Tracks execution time
    - Monitors memory usage (peak and average)
    - Records CPU utilization
    - Generates HTML reports
    - Stores historical data
    """
    
    def __init__(self, output_dir: str = "benchmarks/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process()
        
        # Track system info
        self.system_info = {
            "cpu_count": psutil.cpu_count(),
            "total_memory_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": sys.version,
            "platform": sys.platform
        }
    
    def benchmark(self, func, *args, test_name: str = None, **kwargs):
        """
        Benchmark a function execution
        
        Args:
            func: Function to benchmark
            *args: Function arguments
            test_name: Name for this benchmark
            **kwargs: Function keyword arguments
            
        Returns:
            Function result and BenchmarkResult
        """
        if test_name is None:
            test_name = func.__name__
        
        print(f"\n🔬 Benchmarking: {test_name}")
        
        # Initial measurements
        initial_memory = self.process.memory_info().rss / (1024 * 1024)
        
        # Memory tracking
        memory_samples = []
        cpu_samples = []
        
        def sample_metrics():
            memory_samples.append(self.process.memory_info().rss / (1024 * 1024))
            cpu_samples.append(self.process.cpu_percent(interval=0.1))
        
        # Start benchmark
        start_time = time.time()
        error_message = None
        result = None
        success = True
        
        try:
            # Sample before execution
            sample_metrics()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Sample after execution
            sample_metrics()
            
        except Exception as e:
            success = False
            error_message = str(e)
            print(f"❌ Error: {error_message}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Final measurements
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        
        # Calculate statistics
        peak_memory = max(memory_samples) if memory_samples else final_memory
        avg_memory = statistics.mean(memory_samples) if memory_samples else final_memory
        avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0.0
        memory_used = final_memory - initial_memory
        
        # Create result
        benchmark_result = BenchmarkResult(
            test_name=test_name,
            duration_seconds=duration,
            memory_peak_mb=peak_memory,
            memory_average_mb=avg_memory,
            cpu_percent=avg_cpu,
            success=success,
            error_message=error_message,
            metadata={
                "memory_used_mb": memory_used,
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory
            }
        )
        
        self.results.append(benchmark_result)
        
        # Print results
        print(f"⏱️  Duration: {duration:.2f}s")
        print(f"💾 Memory Peak: {peak_memory:.2f} MB")
        print(f"📊 CPU Usage: {avg_cpu:.1f}%")
        print(f"✅ Status: {'Success' if success else 'Failed'}")
        
        return result, benchmark_result
    
    def generate_summary(self) -> BenchmarkSummary:
        """Generate summary of all benchmarks"""
        if not self.results:
            return BenchmarkSummary(
                total_tests=0,
                successful_tests=0,
                failed_tests=0,
                total_duration=0.0,
                average_duration=0.0,
                peak_memory_mb=0.0,
                average_memory_mb=0.0,
                average_cpu_percent=0.0,
                timestamp=datetime.now().isoformat(),
                results=[]
            )
        
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        
        durations = [r.duration_seconds for r in self.results]
        memories = [r.memory_peak_mb for r in self.results]
        cpus = [r.cpu_percent for r in self.results]
        
        return BenchmarkSummary(
            total_tests=len(self.results),
            successful_tests=len(successful),
            failed_tests=len(failed),
            total_duration=sum(durations),
            average_duration=statistics.mean(durations),
            peak_memory_mb=max(memories),
            average_memory_mb=statistics.mean(memories),
            average_cpu_percent=statistics.mean(cpus),
            timestamp=datetime.now().isoformat(),
            results=[asdict(r) for r in self.results]
        )
    
    def save_results(self, filename: str = None):
        """Save benchmark results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_{timestamp}.json"
        
        output_path = self.output_dir / filename
        summary = self.generate_summary()
        
        data = {
            "summary": asdict(summary),
            "system_info": self.system_info,
            "results": [asdict(r) for r in self.results]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\n💾 Results saved to: {output_path}")
        return output_path
    
    def generate_html_report(self, filename: str = None):
        """Generate HTML report with charts"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_report_{timestamp}.html"
        
        output_path = self.output_dir / filename
        summary = self.generate_summary()
        
        # Generate HTML
        html = self._create_html_report(summary)
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"📊 HTML report generated: {output_path}")
        return output_path
    
    def _create_html_report(self, summary: BenchmarkSummary) -> str:
        """Create HTML report content"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Benchmark Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            margin-top: 0;
            color: #667eea;
        }}
        .metric {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .label {{
            color: #666;
            font-size: 14px;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        .success {{
            color: #22c55e;
        }}
        .failed {{
            color: #ef4444;
        }}
        .system-info {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Performance Benchmark Report</h1>
        <p>Generated: {summary.timestamp}</p>
    </div>
    
    <div class="summary">
        <div class="card">
            <h3>Total Tests</h3>
            <div class="metric">{summary.total_tests}</div>
            <div class="label">✅ {summary.successful_tests} passed · ❌ {summary.failed_tests} failed</div>
        </div>
        
        <div class="card">
            <h3>Total Duration</h3>
            <div class="metric">{summary.total_duration:.2f}s</div>
            <div class="label">Average: {summary.average_duration:.2f}s</div>
        </div>
        
        <div class="card">
            <h3>Peak Memory</h3>
            <div class="metric">{summary.peak_memory_mb:.1f} MB</div>
            <div class="label">Average: {summary.average_memory_mb:.1f} MB</div>
        </div>
        
        <div class="card">
            <h3>CPU Usage</h3>
            <div class="metric">{summary.average_cpu_percent:.1f}%</div>
            <div class="label">Average across all tests</div>
        </div>
    </div>
    
    <div class="card">
        <h2>Detailed Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Name</th>
                    <th>Duration</th>
                    <th>Memory Peak</th>
                    <th>CPU %</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for result in self.results:
            status_class = "success" if result.success else "failed"
            status_text = "✅ Success" if result.success else "❌ Failed"
            
            html += f"""
                <tr>
                    <td>{result.test_name}</td>
                    <td>{result.duration_seconds:.2f}s</td>
                    <td>{result.memory_peak_mb:.1f} MB</td>
                    <td>{result.cpu_percent:.1f}%</td>
                    <td class="{status_class}">{status_text}</td>
                </tr>
"""
        
        html += f"""
            </tbody>
        </table>
    </div>
    
    <div class="system-info">
        <h2>System Information</h2>
        <p><strong>CPU Cores:</strong> {self.system_info['cpu_count']}</p>
        <p><strong>Total RAM:</strong> {self.system_info['total_memory_gb']:.1f} GB</p>
        <p><strong>Platform:</strong> {self.system_info['platform']}</p>
        <p><strong>Python:</strong> {self.system_info['python_version'].split()[0]}</p>
    </div>
</body>
</html>
"""
        return html
    
    def print_summary(self):
        """Print benchmark summary to console"""
        summary = self.generate_summary()
        
        print("\n" + "="*70)
        print("📊 BENCHMARK SUMMARY")
        print("="*70)
        print(f"Total Tests: {summary.total_tests}")
        print(f"✅ Passed: {summary.successful_tests}")
        print(f"❌ Failed: {summary.failed_tests}")
        print(f"\n⏱️  Total Duration: {summary.total_duration:.2f}s")
        print(f"📈 Average Duration: {summary.average_duration:.2f}s")
        print(f"\n💾 Peak Memory: {summary.peak_memory_mb:.1f} MB")
        print(f"📊 Average Memory: {summary.average_memory_mb:.1f} MB")
        print(f"\n🖥️  Average CPU: {summary.average_cpu_percent:.1f}%")
        print("="*70 + "\n")


if __name__ == "__main__":
    # Example usage
    benchmark = PerformanceBenchmark()
    
    # Test function
    def example_task(n):
        """Example computation task"""
        result = sum(i**2 for i in range(n))
        time.sleep(0.5)
        return result
    
    # Run benchmarks
    benchmark.benchmark(example_task, 1000000, test_name="Small Task")
    benchmark.benchmark(example_task, 5000000, test_name="Medium Task")
    benchmark.benchmark(example_task, 10000000, test_name="Large Task")
    
    # Generate reports
    benchmark.print_summary()
    benchmark.save_results()
    benchmark.generate_html_report()
