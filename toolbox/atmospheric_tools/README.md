# Atmospheric Tools

This directory contains tools for atmospheric and meteorological data processing.

## Scripts

### grib2_to_fv3_regrid.py

A Python script that regrids GRIB2 aerosol data to FV3 cube sphere tiles.

**Features:**
- Reads GRIB2 files (e.g., GEFS chemistry products)
- Horizontal interpolation to FV3 cube sphere grid
- Vertical interpolation using ak/bk model coordinates
- Supports orography-based corrections

**Usage:**
```bash
python grib2_to_fv3_regrid.py --input <grib2_file> --orography <oro_file> --akbk <akbk_file> --output <output_dir>
```

**Requirements:**
See requirements.txt for Python dependencies.