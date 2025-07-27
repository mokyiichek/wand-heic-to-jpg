#!/usr/bin/env python3
"""
Configuration module for HEIC converter performance optimization.
Automatically detects system resources and adjusts parameters accordingly.
"""

import os
import psutil
import multiprocessing
from typing import Dict, Any, Optional
from pathlib import Path


class PerformanceConfig:
    """
    Dynamically configure performance parameters based on system resources.
    """
    
    def __init__(self, custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize performance configuration.
        
        Args:
            custom_config: Optional custom configuration overrides
        """
        self.custom_config = custom_config or {}
        self._detect_system_resources()
        self._calculate_optimal_settings()
    
    def _detect_system_resources(self):
        """Detect available system resources."""
        # CPU information
        self.cpu_count = multiprocessing.cpu_count()
        self.cpu_freq = psutil.cpu_freq()
        
        # Memory information
        memory = psutil.virtual_memory()
        self.total_memory_gb = memory.total / (1024**3)
        self.available_memory_gb = memory.available / (1024**3)
        
        # Disk information for common mount points
        self.disk_info = {}
        for mount_point in ['/', '/home', '/tmp']:
            if os.path.exists(mount_point):
                disk_usage = psutil.disk_usage(mount_point)
                self.disk_info[mount_point] = {
                    'total_gb': disk_usage.total / (1024**3),
                    'free_gb': disk_usage.free / (1024**3),
                    'is_ssd': self._detect_ssd(mount_point)
                }
    
    def _detect_ssd(self, mount_point: str) -> bool:
        """
        Attempt to detect if the storage is SSD.
        This is a best-effort detection and may not be 100% accurate.
        """
        try:
            # Check if rotational (0 = SSD, 1 = HDD)
            with open('/sys/block/sda/queue/rotational', 'r') as f:
                return f.read().strip() == '0'
        except:
            # Fallback: assume SSD if we can't determine
            return True
    
    def _calculate_optimal_settings(self):
        """Calculate optimal settings based on detected resources."""
        
        # Base worker count on CPU cores, but adjust for memory and I/O
        base_workers = self.cpu_count
        
        # Reduce workers if memory is limited (< 4GB per worker)
        memory_limited_workers = max(1, int(self.available_memory_gb / 4))
        
        # Adjust for storage type
        storage_multiplier = 1.5 if self._is_primary_storage_ssd() else 0.8
        
        self.optimal_workers = min(
            base_workers,
            memory_limited_workers,
            max(1, int(base_workers * storage_multiplier))
        )
        
        # JPEG quality based on performance vs quality trade-off
        self.optimal_quality = self.custom_config.get('quality', 85)
        
        # Batch size for memory management
        if self.total_memory_gb >= 16:
            self.batch_size = 100
        elif self.total_memory_gb >= 8:
            self.batch_size = 50
        else:
            self.batch_size = 25
        
        # I/O buffer size
        self.io_buffer_size = min(64 * 1024, int(self.available_memory_gb * 1024 * 1024))
    
    def _is_primary_storage_ssd(self) -> bool:
        """Check if primary storage appears to be SSD."""
        return self.disk_info.get('/', {}).get('is_ssd', True)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the complete performance configuration.
        
        Returns:
            Dictionary with optimized configuration parameters
        """
        config = {
            'max_workers': self.optimal_workers,
            'quality': self.optimal_quality,
            'batch_size': self.batch_size,
            'io_buffer_size': self.io_buffer_size,
            'memory_limit_gb': max(2, self.available_memory_gb * 0.8),  # Use 80% of available memory
            
            # System information for debugging
            'system_info': {
                'cpu_count': self.cpu_count,
                'cpu_freq_mhz': self.cpu_freq.current if self.cpu_freq else None,
                'total_memory_gb': round(self.total_memory_gb, 2),
                'available_memory_gb': round(self.available_memory_gb, 2),
                'primary_storage_ssd': self._is_primary_storage_ssd(),
                'disk_info': self.disk_info
            }
        }
        
        # Apply custom overrides
        config.update(self.custom_config)
        return config
    
    def print_config(self):
        """Print the current configuration in a readable format."""
        config = self.get_config()
        
        print("Performance Configuration:")
        print("=" * 40)
        print(f"Workers: {config['max_workers']}")
        print(f"JPEG Quality: {config['quality']}")
        print(f"Batch Size: {config['batch_size']}")
        print(f"Memory Limit: {config['memory_limit_gb']:.1f} GB")
        print(f"I/O Buffer: {config['io_buffer_size'] // 1024} KB")
        print()
        
        print("System Information:")
        print("-" * 20)
        sys_info = config['system_info']
        print(f"CPU Cores: {sys_info['cpu_count']}")
        if sys_info['cpu_freq_mhz']:
            print(f"CPU Frequency: {sys_info['cpu_freq_mhz']:.0f} MHz")
        print(f"Total Memory: {sys_info['total_memory_gb']} GB")
        print(f"Available Memory: {sys_info['available_memory_gb']} GB")
        print(f"Primary Storage SSD: {sys_info['primary_storage_ssd']}")


# Predefined configurations for different scenarios
PERFORMANCE_PROFILES = {
    'fast': {
        'quality': 75,
        'max_workers': None,  # Use auto-detection
        'batch_size': None,   # Use auto-detection
    },
    
    'balanced': {
        'quality': 85,
        'max_workers': None,
        'batch_size': None,
    },
    
    'quality': {
        'quality': 95,
        'max_workers': None,
        'batch_size': None,
    },
    
    'memory_conservative': {
        'quality': 85,
        'max_workers': 2,
        'batch_size': 10,
        'memory_limit_gb': 2,
    },
    
    'cpu_intensive': {
        'quality': 85,
        'max_workers': None,  # Will use all available cores
        'batch_size': None,
    }
}


def get_profile_config(profile_name: str) -> PerformanceConfig:
    """
    Get a pre-configured performance profile.
    
    Args:
        profile_name: Name of the profile ('fast', 'balanced', 'quality', etc.)
        
    Returns:
        PerformanceConfig instance with the specified profile
    """
    if profile_name not in PERFORMANCE_PROFILES:
        raise ValueError(f"Unknown profile: {profile_name}. Available: {list(PERFORMANCE_PROFILES.keys())}")
    
    profile_config = PERFORMANCE_PROFILES[profile_name]
    return PerformanceConfig(custom_config=profile_config)


if __name__ == "__main__":
    # Demo the configuration system
    print("Auto-detected Configuration:")
    config = PerformanceConfig()
    config.print_config()
    
    print("\n" + "=" * 50)
    print("Available Performance Profiles:")
    for profile_name in PERFORMANCE_PROFILES:
        print(f"\n{profile_name.upper()} Profile:")
        profile_config = get_profile_config(profile_name)
        profile_config.print_config()