#!/usr/bin/env python3
"""
Example usage of the GRIB2 to FV3 regridding tool.

This script demonstrates how to use the regridding tool with sample data.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_example():
    """Run an example of the regridding tool."""
    
    # Get the script directory
    script_dir = Path(__file__).parent
    regrid_script = script_dir / "grib2_to_fv3_regrid.py"
    
    print("GRIB2 to FV3 Regridding Tool - Example Usage")
    print("=" * 50)
    print()
    
    # Example 1: Basic usage with orography files
    print("Example 1: Basic regridding with orography files")
    print("-" * 30)
    
    sample_input = "gefs.chem.t12z.a3d_0p50.f000.grib2"
    sample_output = "output_tiles"
    oro_prefix = "C384_oro_"
    
    cmd = [
        sys.executable, str(regrid_script),
        "--input", sample_input,
        "--orography-prefix", oro_prefix,
        "--output", sample_output,
        "--npx", "384",
        "--method", "linear"
    ]
    
    print("Command:")
    print(" ".join(cmd))
    print()
    print("This requires orography files:")
    print("- C384_oro_tile1.nc")
    print("- C384_oro_tile2.nc")
    print("- C384_oro_tile3.nc")
    print("- C384_oro_tile4.nc")
    print("- C384_oro_tile5.nc")
    print("- C384_oro_tile6.nc")
    print()
    print("Each file must contain geolon and geolat coordinate variables.")
    print()
    
    # Example 2: With field mapping and vertical interpolation
    print("Example 2: With field mapping and vertical interpolation")
    print("-" * 30)
    
    cmd2 = [
        sys.executable, str(regrid_script),
        "--input", sample_input,
        "--orography-prefix", oro_prefix,
        "--field-mapping", "aerosol_mapping.yaml",
        "--akbk", "akbk_L127.nc",
        "--output", sample_output,
        "--npx", "384",
        "--method", "cubic",
        "--verbose"
    ]
    
    print("Command:")
    print(" ".join(cmd2))
    print()
    print("This requires:")
    print("- Orography files for each tile")
    print("- aerosol_mapping.yaml file with field mappings")
    print("- akbk_L127.nc file with ak/bk coefficients")
    print()
    print("Example aerosol_mapping.yaml:")
    print("---")
    print('"Mass Density": "dust"')
    print('"Aerosol Optical Depth": "aod"')
    print('"Sulfate": "so4"')
    print()
    
    # Example 3: Different grid resolutions  
    print("Example 3: Different grid resolutions")
    print("-" * 30)
    
    resolutions = [48, 96, 192, 384, 768]
    
    for res in resolutions:
        cmd3 = [
            sys.executable, str(regrid_script),
            "--input", sample_input,
            "--orography-prefix", f"C{res}_oro_",
            "--output", f"output_C{res}",
            "--npx", str(res)
        ]
        print(f"C{res:3d}: {' '.join(cmd3)}")
    
    print()
    print("These commands would create outputs for different FV3 resolutions:")
    print("- C48:  48x48 points per tile (coarse)")
    print("- C96:  96x96 points per tile")  
    print("- C192: 192x192 points per tile")
    print("- C384: 384x384 points per tile (standard)")
    print("- C768: 768x768 points per tile (high resolution)")
    print()
    
    # Data sources
    print("Data Sources")
    print("-" * 30)
    print("GEFS Chemistry GRIB2 files can be found at:")
    print("https://nomads.ncep.noaa.gov/pub/data/nccf/com/gens/prod/")
    print()
    print("Example file paths:")
    print("- gefs.20250717/12/chem/pgrb2ap5/gefs.chem.t12z.a3d_0p50.f000.grib2")
    print("- gefs.20250717/12/chem/pgrb2ap5/gefs.chem.t12z.a3d_0p50.f006.grib2")
    print()
    print("FV3 grid files and ak/bk coefficients would typically come from:")
    print("- UFS weather model repository")
    print("- FV3 grid generation tools")
    print("- Model configuration files")
    print()
    
    # Output format
    print("Output Format")
    print("-" * 30)
    print("The tool creates netCDF files for each of the 6 cube sphere tiles:")
    print("- aerosol_tile1.nc")
    print("- aerosol_tile2.nc")
    print("- aerosol_tile3.nc")
    print("- aerosol_tile4.nc")
    print("- aerosol_tile5.nc")
    print("- aerosol_tile6.nc")
    print()
    print("Each file contains regridded aerosol fields with proper metadata.")
    print()

if __name__ == "__main__":
    run_example()