#!/usr/bin/env python3
"""
Optimized HEIC to JPG converter with performance improvements:
- Parallel processing using multiprocessing
- Better memory management
- Efficient directory traversal
- Progress tracking
- Improved error handling
- Configurable quality settings
"""

import os
import sys
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
from wand.image import Image
from wand.exceptions import WandException
import argparse
from typing import List, Tuple, Optional


class HEICConverter:
    def __init__(self, 
                 base_paths: List[str], 
                 skip_dirs: List[str] = None,
                 max_workers: Optional[int] = None,
                 quality: int = 85,
                 verbose: bool = True):
        """
        Initialize the HEIC converter.
        
        Args:
            base_paths: List of base directories to scan
            skip_dirs: Directories to skip during traversal
            max_workers: Number of parallel workers (default: CPU count)
            quality: JPEG quality (1-100, default: 85)
            verbose: Enable verbose output
        """
        self.base_paths = base_paths
        self.skip_dirs = skip_dirs or ['.sync', '.git', '__pycache__', '.DS_Store']
        self.max_workers = max_workers or min(cpu_count(), 8)  # Cap at 8 to avoid memory issues
        self.quality = quality
        self.verbose = verbose
        
    def find_heic_files(self) -> List[Tuple[str, str]]:
        """
        Efficiently find all HEIC files and their target JPG paths.
        
        Returns:
            List of tuples (source_path, target_path)
        """
        heic_files = []
        
        for base_path in self.base_paths:
            if not os.path.exists(base_path):
                if self.verbose:
                    print(f"Warning: Base path does not exist: {base_path}")
                continue
                
            # Use pathlib for more efficient directory traversal
            base_path_obj = Path(base_path)
            
            # Use glob for efficient pattern matching
            for heic_file in base_path_obj.rglob("*.HEIC"):
                # Check if we should skip this directory
                if any(skip_dir in heic_file.parts for skip_dir in self.skip_dirs):
                    continue
                    
                source_path = str(heic_file)
                target_path = str(heic_file.with_suffix('.JPG'))
                
                # Skip if JPG already exists and has content
                if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                    if self.verbose:
                        print(f"Skipping {heic_file.name} - JPG already exists")
                    continue
                    
                heic_files.append((source_path, target_path))
        
        return heic_files
    
    @staticmethod
    def convert_single_file(args: Tuple[str, str, int, bool]) -> Tuple[bool, str, str]:
        """
        Convert a single HEIC file to JPG.
        
        Args:
            args: Tuple of (source_path, target_path, quality, verbose)
            
        Returns:
            Tuple of (success, source_path, message)
        """
        source_path, target_path, quality, verbose = args
        
        try:
            # Use context manager for automatic resource cleanup
            with Image(filename=source_path) as img:
                # Set JPEG quality
                img.compression_quality = quality
                img.format = 'jpeg'
                
                # Save the converted image
                img.save(filename=target_path)
                
            return True, source_path, f"Successfully converted to {target_path}"
            
        except WandException as e:
            return False, source_path, f"Wand error: {str(e)}"
        except OSError as e:
            return False, source_path, f"File system error: {str(e)}"
        except Exception as e:
            return False, source_path, f"Unexpected error: {str(e)}"
    
    def convert_files(self) -> Tuple[int, int]:
        """
        Convert all HEIC files using parallel processing.
        
        Returns:
            Tuple of (successful_conversions, failed_conversions)
        """
        heic_files = self.find_heic_files()
        
        if not heic_files:
            if self.verbose:
                print("No HEIC files found to convert.")
            return 0, 0
        
        if self.verbose:
            print(f"Found {len(heic_files)} HEIC files to convert")
            print(f"Using {self.max_workers} parallel workers")
            print(f"JPEG quality set to {self.quality}")
        
        successful = 0
        failed = 0
        start_time = time.time()
        
        # Prepare arguments for parallel processing
        conversion_args = [
            (source, target, self.quality, self.verbose) 
            for source, target in heic_files
        ]
        
        # Use ProcessPoolExecutor for CPU-bound image processing
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all conversion jobs
            future_to_file = {
                executor.submit(self.convert_single_file, args): args[0] 
                for args in conversion_args
            }
            
            # Process completed conversions
            for future in as_completed(future_to_file):
                source_file = future_to_file[future]
                
                try:
                    success, source_path, message = future.result()
                    
                    if success:
                        successful += 1
                        if self.verbose:
                            print(f"✓ {Path(source_path).name}: {message}")
                    else:
                        failed += 1
                        if self.verbose:
                            print(f"✗ {Path(source_path).name}: {message}")
                            
                    # Progress indicator
                    if self.verbose and (successful + failed) % 10 == 0:
                        total_processed = successful + failed
                        progress = (total_processed / len(heic_files)) * 100
                        elapsed = time.time() - start_time
                        rate = total_processed / elapsed if elapsed > 0 else 0
                        print(f"Progress: {progress:.1f}% ({total_processed}/{len(heic_files)}) - {rate:.1f} files/sec")
                        
                except Exception as e:
                    failed += 1
                    if self.verbose:
                        print(f"✗ {Path(source_file).name}: Process execution error: {str(e)}")
        
        elapsed_time = time.time() - start_time
        
        if self.verbose:
            print(f"\nConversion completed in {elapsed_time:.2f} seconds")
            print(f"Successful: {successful}")
            print(f"Failed: {failed}")
            print(f"Average rate: {len(heic_files) / elapsed_time:.2f} files/sec")
        
        return successful, failed


def main():
    """Main function with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Optimized HEIC to JPG converter with parallel processing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'paths', 
        nargs='+', 
        help='Base directories to scan for HEIC files'
    )
    
    parser.add_argument(
        '--workers', 
        type=int, 
        default=None,
        help='Number of parallel workers (default: CPU count, max 8)'
    )
    
    parser.add_argument(
        '--quality', 
        type=int, 
        default=85,
        choices=range(1, 101),
        metavar='1-100',
        help='JPEG quality (1-100)'
    )
    
    parser.add_argument(
        '--skip-dirs',
        nargs='*',
        default=['.sync', '.git', '__pycache__', '.DS_Store'],
        help='Directories to skip during traversal'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress verbose output'
    )
    
    args = parser.parse_args()
    
    # Create converter instance
    converter = HEICConverter(
        base_paths=args.paths,
        skip_dirs=args.skip_dirs,
        max_workers=args.workers,
        quality=args.quality,
        verbose=not args.quiet
    )
    
    # Perform conversion
    try:
        successful, failed = converter.convert_files()
        
        # Exit with appropriate code
        if failed > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    # For backward compatibility, also support the original hardcoded paths
    if len(sys.argv) == 1:
        # Use original hardcoded paths if no arguments provided
        basepaths = ['/user/folder1/images', '/user/folder2/images']
        converter = HEICConverter(base_paths=basepaths)
        converter.convert_files()
    else:
        main()