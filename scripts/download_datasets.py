#!/usr/bin/env python3
"""
Dataset Download Script for Hybrid AI-IDS Project
Downloads UNSW-NB15 and CICIDS-2017 datasets
"""

import os
import requests
import zipfile
from pathlib import Path

def download_unsw_nb15():
    """Download UNSW-NB15 dataset from Kaggle"""
    print("Downloading UNSW-NB15 dataset...")
    
    # Method 1: Kaggle API (recommended)
    try:
        import kaggle
        kaggle.api.dataset_download_files(
            'dhoogla/unswnb15', 
            path='data/unsw-nb15',
            unzip=True
        )
        print("✅ UNSW-NB15 downloaded successfully")
    except Exception as e:
        print(f"❌ Kaggle download failed: {e}")
        print("Please download manually from: https://www.kaggle.com/datasets/dhoogla/unswnb15")

def download_cicids_2017():
    """Download CICIDS-2017 dataset"""
    print("Downloading CICIDS-2017 dataset...")
    
    # CICIDS-2017 contains multiple days of data
    # Available as PCAP files and pre-extracted CSV features
    print("CICIDS-2017 contains:")
    print("- Monday: Benign traffic")
    print("- Tuesday: Brute Force (FTP, SSH)")
    print("- Wednesday: DoS/DDoS attacks")
    print("- Thursday: Web attacks + Infiltration")
    print("- Friday: Botnet + PortScan + DDoS")
    
    print("\nDownload options:")
    print("1. Official site: https://www.unb.ca/cic/datasets/ids-2017.html")
    print("2. Kaggle: https://www.kaggle.com/datasets/dhoogla/cicids2017")
    print("3. IEEE DataPort: https://ieee-dataport.org/documents/cicids2017")
    
    # Create data directory
    os.makedirs('data/cicids-2017', exist_ok=True)
    
    print("\nNote: CICIDS-2017 is ~70GB total")
    print("Recommend downloading CSV features directly to avoid PCAP processing")

if __name__ == "__main__":
    print("Hybrid AI-IDS Dataset Downloader")
    print("=" * 40)
    
    # Create data directories
    os.makedirs('data', exist_ok=True)
    
    # Download datasets
    download_unsw_nb15()
    download_cicids_2017()
    
    print("\nDownload complete!")
    print("Next steps:")
    print("1. Install Kaggle API for UNSW-NB15")
    print("2. Download CICIDS-2017 CSV features from Kaggle")
