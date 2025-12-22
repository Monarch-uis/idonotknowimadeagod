"""
EPUB Converter Component Benchmarks
Benchmarks for specific conversion components
"""
import sys
from pathlib import Path
import time
import tempfile
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.performance_benchmark import PerformanceBenchmark
from core.utils import sanitize_filename, censor_text, fix_pronunciation
from core.epub_io import clean_html_for_tts


def benchmark_text_processing():
    """Benchmark text processing functions"""
    print("\n🔬 Benchmarking Text Processing")
    benchmark = PerformanceBenchmark(output_dir="benchmarks/results")
    
    # Test data
    long_text = "Test text " * 10000
    html_content = f"<p>{'Test paragraph ' * 1000}</p>" * 50
    
    # Benchmark sanitization
    benchmark.benchmark(
        lambda: [sanitize_filename(f"Chapter {i}: Test") for i in range(1000)],
        test_name="Filename Sanitization (1000 files)"
    )
    
    # Benchmark censoring
    benchmark.benchmark(
        lambda: censor_text(long_text),
        test_name="Text Censoring (100k words)"
    )
    
    # Benchmark HTML cleaning
    benchmark.benchmark(
        lambda: clean_html_for_tts(html_content),
        test_name="HTML Cleaning (50k chars)"
    )
    
    # Benchmark pronunciation fixes
    test_text = "Naruto and Sasuke from Konoha "  * 1000
    benchmark.benchmark(
        lambda: fix_pronunciation(test_text),
        test_name="Pronunciation Fixes (3k words)"
    )
    
    benchmark.print_summary()
    benchmark.save_results("text_processing_benchmark.json")
    benchmark.generate_html_report("text_processing_report.html")


def benchmark_file_operations():
    """Benchmark file I/O operations"""
    print("\n🔬 Benchmarking File Operations")
    benchmark = PerformanceBenchmark(output_dir="benchmarks/results")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Benchmark file creation
        def create_files():
            for i in range(100):
                file_path = temp_path / f"test_{i}.txt"
                file_path.write_text("Test content " * 1000)
        
        benchmark.benchmark(
            create_files,
            test_name="Create 100 Text Files"
        )
        
        # Benchmark file reading
        def read_files():
            files = list(temp_path.glob("*.txt"))
            return [f.read_text() for f in files]
        
        benchmark.benchmark(
            read_files,
            test_name="Read 100 Text Files"
        )
    
    benchmark.print_summary()
    benchmark.save_results("file_operations_benchmark.json")
    benchmark.generate_html_report("file_operations_report.html")


def benchmark_batch_processing():
    """Benchmark batch processing scenarios"""
    print("\n🔬 Benchmarking Batch Processing")
    benchmark = PerformanceBenchmark(output_dir="benchmarks/results")
    
    # Simulate chapter processing
    def process_small_batch():
        """Process 10 chapters"""
        chapters = [f"Chapter {i} content " * 1000 for i in range(10)]
        processed = []
        for chapter in chapters:
            # Simulate processing
            cleaned = clean_html_for_tts(f"<p>{chapter}</p>")
            processed.append(cleaned)
        return processed
    
    def process_medium_batch():
        """Process 50 chapters"""
        chapters = [f"Chapter {i} content " * 1000 for i in range(50)]
        processed = []
        for chapter in chapters:
            cleaned = clean_html_for_tts(f"<p>{chapter}</p>")
            processed.append(cleaned)
        return processed
    
    def process_large_batch():
        """Process 100 chapters"""
        chapters = [f"Chapter {i} content " * 1000 for i in range(100)]
        processed = []
        for chapter in chapters:
            cleaned = clean_html_for_tts(f"<p>{chapter}</p>")
            processed.append(cleaned)
        return processed
    
    benchmark.benchmark(process_small_batch, test_name="Batch: 10 Chapters")
    benchmark.benchmark(process_medium_batch, test_name="Batch: 50 Chapters")
    benchmark.benchmark(process_large_batch, test_name="Batch: 100 Chapters")
    
    benchmark.print_summary()
    benchmark.save_results("batch_processing_benchmark.json")
    benchmark.generate_html_report("batch_processing_report.html")


def benchmark_memory_intensive():
    """Benchmark memory-intensive operations"""
    print("\n🔬 Benchmarking Memory-Intensive Operations")
    benchmark = PerformanceBenchmark(output_dir="benchmarks/results")
    
    # Large data processing
    def process_large_data():
        # Simulate large book (1000 chapters, 5000 words each)
        data = []
        for i in range(1000):
            chapter = {
                "number": i,
                "title": f"Chapter {i}",
                "text": "word " * 5000
            }
            data.append(chapter)
        return data
    
    benchmark.benchmark(
        process_large_data,
        test_name="Load Large Book (1000 chapters, 5M words)"
    )
    
    # Multiple processing passes
    def multi_pass_processing():
        data = ["Test " * 10000 for _ in range(100)]
        # Pass 1: Clean
        cleaned = [clean_html_for_tts(f"<p>{d}</p>") for d in data]
        # Pass 2: Censor
        censored = [censor_text(d) for d in cleaned]
        return censored
    
    benchmark.benchmark(
        multi_pass_processing,
        test_name="Multi-Pass Processing (100 items)"
    )
    
    benchmark.print_summary()
    benchmark.save_results("memory_intensive_benchmark.json")
    benchmark.generate_html_report("memory_intensive_report.html")


def run_all_benchmarks():
    """Run all benchmarks"""
    print("\n" + "="*70)
    print("🚀 RUNNING ALL EPUB CONVERTER BENCHMARKS")
    print("="*70)
    
    benchmark_text_processing()
    benchmark_file_operations()
    benchmark_batch_processing()
    benchmark_memory_intensive()
    
    print("\n" + "="*70)
    print("✅ ALL BENCHMARKS COMPLETE!")
    print("📊 Check benchmarks/results/ for detailed reports")
    print("="*70 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run EPUB converter benchmarks")
    parser.add_argument(
        "--test",
        choices=["text", "files", "batch", "memory", "all"],
        default="all",
        help="Which benchmark to run"
    )
    
    args = parser.parse_args()
    
    if args.test == "text":
        benchmark_text_processing()
    elif args.test == "files":
        benchmark_file_operations()
    elif args.test == "batch":
        benchmark_batch_processing()
    elif args.test == "memory":
        benchmark_memory_intensive()
    else:
        run_all_benchmarks()
