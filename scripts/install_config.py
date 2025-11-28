#!/usr/bin/env python
"""
Hiero Review Tool - Configuration Installer
============================================
Copies project configuration files to the user's .nuke directory.

Usage:
    python install_config.py
"""
import os
import sys
import shutil
from pathlib import Path


def get_config_source_dir() -> Path:
    """Get the source config directory (bundled with the tool)."""
    return Path(__file__).parent.parent / 'config'


def get_config_target_dir() -> Path:
    """Get the target config directory (~/.nuke/hiero_review_projects)."""
    return Path.home() / ".nuke" / "hiero_review_projects"


def install_configs(force: bool = False) -> None:
    """Install configuration files to user's .nuke directory."""
    source_dir = get_config_source_dir()
    target_dir = get_config_target_dir()
    
    if not source_dir.exists():
        print(f"Error: Source config directory not found: {source_dir}")
        sys.exit(1)
    
    # Create target directory if it doesn't exist
    target_dir.mkdir(parents=True, exist_ok=True)
    print(f"Config directory: {target_dir}")
    
    # Copy each config file
    config_files = list(source_dir.glob("*.json"))
    if not config_files:
        print("No configuration files found to install.")
        return
    
    for config_file in config_files:
        target_file = target_dir / config_file.name
        
        if target_file.exists() and not force:
            print(f"  Skipping {config_file.name} (already exists, use --force to overwrite)")
            continue
        
        shutil.copy2(config_file, target_file)
        print(f"  Installed: {config_file.name}")
    
    print("\nConfiguration files installed successfully!")
    print(f"\nTo customize, edit the JSON files in: {target_dir}")


def main():
    """Main entry point."""
    force = '--force' in sys.argv or '-f' in sys.argv
    
    print("=" * 50)
    print("Hiero Review Tool - Configuration Installer")
    print("=" * 50)
    print()
    
    install_configs(force=force)


if __name__ == '__main__':
    main()

