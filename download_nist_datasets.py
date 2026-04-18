"""
download_nist_datasets.py
Downloads NIST AM Bench datasets directly from the NIST PDR.
Run this first before the converter script.
"""

import urllib.request
import os

print("Downloading NIST AM Bench datasets...")
print("Source: https://data.nist.gov (NIST Public Data Repository)")
print()

# Create a folder for raw NIST data
os.makedirs("nist_raw_data", exist_ok=True)

datasets = [
    {
        "name": "AMB2018-03 Polymer FDM Tensile Properties",
        "url": "https://data.nist.gov/od/ds/mds2-2363/AMB2018-03_Tensile_Properties.csv",
        "filename": "nist_raw_data/AMB2018_03_tensile.csv",
        "fallback": True
    },
    {
        "name": "AMB2018-04 Polyamide 12 Properties",
        "url": "https://data.nist.gov/od/ds/mds2-2364/AMB2018-04_Physical_Properties.csv",
        "filename": "nist_raw_data/AMB2018_04_polyamide.csv",
        "fallback": True
    },
]

for ds in datasets:
    print(f"Downloading: {ds['name']}")
    try:
        urllib.request.urlretrieve(ds["url"], ds["filename"])
        size = os.path.getsize(ds["filename"])
        print(f"  Saved → {ds['filename']} ({size} bytes)")
    except Exception as e:
        print(f"  Could not auto-download: {e}")
        print(f"  Manual download: visit https://data.nist.gov and search for {ds['name'][:20]}")
        print(f"  Save the CSV to: {ds['filename']}")
    print()

print("If auto-download failed, use the NIST-inspired dataset instead:")
print("  python generate_nist_inspired_dataset.py")