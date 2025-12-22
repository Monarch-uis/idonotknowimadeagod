# Performance Benchmarks

Comprehensive performance testing and monitoring for the EPUB converter.

## Overview

The benchmark suite tracks:
- ⏱️ **Execution Time** - How long operations take
- 💾 **Memory Usage** - Peak and average RAM consumption
- 🖥️ **CPU Usage** - Processor utilization
- 📊 **Reports** - HTML and JSON output

## Quick Start

### Run All Benchmarks

```bash
python benchmarks/component_benchmarks.py
```

### Run Specific Benchmarks

```bash
# Text processing only
python benchmarks/component_benchmarks.py --test text

# File operations
python benchmarks/component_benchmarks.py --test files

# Batch processing
python benchmarks/component_benchmarks.py --test batch

# Memory intensive
python benchmarks/component_benchmarks.py --test memory
```

### Using Makefile

```bash
# Run benchmarks
make benchmark

# View last benchmark report
make benchmark-view
```

## Output

Benchmarks generate two types of reports:

### 1. JSON Reports
Located in `benchmarks/results/`:
- Machine-readable format
- Historical data storage
- Can be processed programmatically

### 2. HTML Reports
Interactive reports with:
- Visual charts and graphs
- Detailed metrics
- System information
- Pass/fail status

## Example Output

```
🔬 Benchmarking: Text Processing
⏱️  Duration: 1.23s
💾 Memory Peak: 245.6 MB
📊 CPU Usage: 87.3%
✅ Status: Success

📊 BENCHMARK SUMMARY
==================================================
Total Tests: 4
✅ Passed: 4
❌ Failed: 0

⏱️  Total Duration: 5.67s
📈 Average Duration: 1.42s

💾 Peak Memory: 512.3 MB
📊 Average Memory: 387.9 MB

🖥️  Average CPU: 78.4%
==================================================
```

## Custom Benchmarks

Create your own benchmarks:

```python
from benchmarks.performance_benchmark import PerformanceBenchmark

# Initialize
benchmark = PerformanceBenchmark()

# Benchmark a function
def my_function():
    # Your code here
    pass

result, metrics = benchmark.benchmark(
    my_function,
    test_name="My Custom Test"
)

# Generate reports
benchmark.print_summary()
benchmark.save_results()
benchmark.generate_html_report()
```

## Interpreting Results

### Good Performance
- ✅ Duration < 5s for batch processing
- ✅ Memory < 500MB for typical books
- ✅ CPU < 90% average

### Needs Optimization
- ⚠️ Duration > 10s
- ⚠️ Memory > 1GB
- ⚠️ CPU > 95%

### Critical Issues
- ❌ Memory growth over time (leak)
- ❌ CPU pinned at 100%
- ❌ Crashes or timeouts

## Continuous Monitoring

Run benchmarks regularly to:
1. Track performance changes over time
2. Identify regressions
3. Validate optimizations
4. Set performance baselines

## Integration with CI/CD

Add to your workflow:

```yaml
- name: Run Benchmarks
  run: python benchmarks/component_benchmarks.py

- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: benchmark-reports
    path: benchmarks/results/
```

## Troubleshooting

**High Memory Usage:**
- Reduce batch size in config
- Enable memory optimization
- Check for memory leaks

**Slow Performance:**
- Enable concurrent processing
- Use faster quality presets
- Optimize batch size

**Inconsistent Results:**
- Close other applications
- Run multiple times
- Check system resources
