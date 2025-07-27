#!/usr/bin/env python3
"""
Benchmark script to compare performance between original and optimized HEIC converters.
"""

import os
import time
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple, List
import argparse


def create_test_structure(base_dir: str, num_dirs: int = 5, files_per_dir: int = 3) -> List[str]:
    """
    Create a test directory structure with dummy HEIC files for benchmarking.
    
    Args:
        base_dir: Base directory to create test structure in
        num_dirs: Number of subdirectories to create
        files_per_dir: Number of HEIC files per directory
        
    Returns:
        List of created HEIC file paths
    """
    created_files = []
    base_path = Path(base_dir)
    
    # Create a simple test HEIC-like file (just empty file for structure testing)
    for i in range(num_dirs):
        dir_path = base_path / f"test_dir_{i}"
        dir_path.mkdir(parents=True, exist_ok=True)
        
        for j in range(files_per_dir):
            heic_file = dir_path / f"test_image_{j}.HEIC"
            # Create a small dummy file
            heic_file.write_bytes(b"dummy_heic_content")
            created_files.append(str(heic_file))
            
    # Create some directories that should be skipped
    skip_dir = base_path / ".git"
    skip_dir.mkdir(exist_ok=True)
    skip_file = skip_dir / "should_be_skipped.HEIC"
    skip_file.write_bytes(b"should_not_process")
    
    return created_files


def benchmark_directory_traversal(base_paths: List[str]) -> Tuple[float, int]:
    """
    Benchmark directory traversal performance.
    
    Returns:
        Tuple of (time_taken, files_found)
    """
    from convert_optimized import HEICConverter
    
    start_time = time.time()
    converter = HEICConverter(base_paths=base_paths, verbose=False)
    heic_files = converter.find_heic_files()
    end_time = time.time()
    
    return end_time - start_time, len(heic_files)


def benchmark_original_traversal(base_paths: List[str]) -> Tuple[float, int]:
    """
    Benchmark the original directory traversal method.
    """
    import os
    
    findfile = '.HEIC'
    skipdirs = ['.sync', '.git', '__pycache__']
    files_found = 0
    
    def check_dir_original(path, file, level=0):
        nonlocal files_found
        
        for entry_path in os.listdir(path):
            if os.path.isdir(os.path.join(path, entry_path)):
                if not entry_path in skipdirs:
                    check_dir_original(os.path.join(path, entry_path), file, level+1)
                
                for entry_file in os.listdir(os.path.join(path, entry_path)):
                    if entry_file.endswith(file):
                        files_found += 1
    
    start_time = time.time()
    for base_path in base_paths:
        if os.path.exists(base_path):
            check_dir_original(base_path, findfile)
    end_time = time.time()
    
    return end_time - start_time, files_found


def measure_memory_usage():
    """
    Provide memory usage measurement suggestions.
    """
    print("\nMemory Usage Analysis:")
    print("=" * 50)
    print("To measure memory usage, you can use:")
    print("1. For overall process memory:")
    print("   python -m memory_profiler convert_optimized.py [paths]")
    print("   (requires: pip install memory-profiler)")
    print()
    print("2. For line-by-line memory profiling:")
    print("   kernprof -l -v convert_optimized.py")
    print("   (requires: pip install line_profiler)")
    print()
    print("3. Using system monitoring:")
    print("   htop or top while running conversions")


def analyze_bundle_size():
    """
    Analyze the 'bundle size' equivalent for Python scripts.
    """
    print("\nCode Size Analysis:")
    print("=" * 50)
    
    files_to_analyze = ['convert.py', 'convert_optimized.py']
    
    for filename in files_to_analyze:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            with open(filename, 'r') as f:
                lines = len(f.readlines())
                
            print(f"{filename}:")
            print(f"  File size: {size} bytes")
            print(f"  Lines of code: {lines}")
            print(f"  Bytes per line: {size/lines:.1f}")
            print()


def run_performance_comparison(test_dirs: List[str], iterations: int = 3):
    """
    Run performance comparison between original and optimized versions.
    """
    print(f"\nPerformance Comparison ({iterations} iterations):")
    print("=" * 60)
    
    # Benchmark directory traversal
    original_times = []
    optimized_times = []
    
    for i in range(iterations):
        print(f"Iteration {i+1}/{iterations}")
        
        # Original method
        orig_time, orig_files = benchmark_original_traversal(test_dirs)
        original_times.append(orig_time)
        
        # Optimized method
        opt_time, opt_files = benchmark_directory_traversal(test_dirs)
        optimized_times.append(opt_time)
        
        print(f"  Original: {orig_time:.4f}s ({orig_files} files)")
        print(f"  Optimized: {opt_time:.4f}s ({opt_files} files)")
        print(f"  Speedup: {orig_time/opt_time:.2f}x")
        print()
    
    # Calculate averages
    avg_original = sum(original_times) / len(original_times)
    avg_optimized = sum(optimized_times) / len(optimized_times)
    avg_speedup = avg_original / avg_optimized
    
    print("Average Results:")
    print(f"  Original method: {avg_original:.4f}s")
    print(f"  Optimized method: {avg_optimized:.4f}s")
    print(f"  Average speedup: {avg_speedup:.2f}x")
    print(f"  Performance improvement: {((avg_speedup - 1) * 100):.1f}%")


def main():
    """Main benchmark function."""
    parser = argparse.ArgumentParser(description="Benchmark HEIC converter performance")
    parser.add_argument('--test-dirs', type=int, default=5, help='Number of test directories')
    parser.add_argument('--files-per-dir', type=int, default=10, help='Files per directory')
    parser.add_argument('--iterations', type=int, default=3, help='Benchmark iterations')
    parser.add_argument('--temp-dir', type=str, help='Custom temporary directory')
    
    args = parser.parse_args()
    
    print("HEIC Converter Performance Benchmark")
    print("=" * 40)
    
    # Create temporary test environment
    if args.temp_dir:
        temp_dir = args.temp_dir
        os.makedirs(temp_dir, exist_ok=True)
    else:
        temp_dir = tempfile.mkdtemp(prefix="heic_benchmark_")
    
    try:
        print(f"Creating test structure in: {temp_dir}")
        test_files = create_test_structure(
            temp_dir, 
            num_dirs=args.test_dirs, 
            files_per_dir=args.files_per_dir
        )
        print(f"Created {len(test_files)} test files")
        
        # Analyze code size
        analyze_bundle_size()
        
        # Run performance comparison
        run_performance_comparison([temp_dir], iterations=args.iterations)
        
        # Memory usage suggestions
        measure_memory_usage()
        
        # Additional optimization suggestions
        print("\nAdditional Optimization Opportunities:")
        print("=" * 50)
        print("1. Image Processing:")
        print("   - Use different image libraries (Pillow, OpenCV) for comparison")
        print("   - Implement progressive JPEG encoding")
        print("   - Add image resizing options to reduce file sizes")
        print()
        print("2. I/O Optimizations:")
        print("   - Implement asynchronous file operations")
        print("   - Use memory mapping for large files")
        print("   - Add SSD vs HDD detection for optimal worker count")
        print()
        print("3. Batch Processing:")
        print("   - Process files in batches to reduce memory pressure")
        print("   - Implement queue-based processing for very large datasets")
        print("   - Add resume capability for interrupted conversions")
        
    finally:
        # Cleanup
        if not args.temp_dir:  # Only cleanup if we created the temp dir
            print(f"\nCleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()