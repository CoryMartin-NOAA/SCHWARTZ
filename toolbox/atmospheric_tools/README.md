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
# Basic usage with orography files for each tile
python grib2_to_fv3_regrid.py \
  --input <grib2_file> \
  --orography-prefix <prefix> \
  --output <output_dir>

# With field mapping and vertical interpolation
python grib2_to_fv3_regrid.py \
  --input <grib2_file> \
  --orography-prefix <prefix> \
  --field-mapping <mapping.yaml> \
  --akbk <akbk_file> \
  --output <output_dir>
```

**Orography Files:**
The tool expects one orography file per tile named `{prefix}tile{N}.nc` where N is 1-6.
Each file must contain `geolon` and `geolat` coordinate variables.

**Field Mapping:**
Optional YAML file to map GRIB2 field names to output variable names:
```yaml
"Mass Density": "dust"
"Aerosol Optical Depth": "aod"
```

**Requirements:**
See requirements.txt for Python dependencies.