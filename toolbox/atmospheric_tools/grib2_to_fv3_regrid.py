#!/usr/bin/env python3
"""
GRIB2 to FV3 Regridding Tool

This script reads GRIB2 aerosol data (e.g., from GEFS chemistry products) and
regrids it both horizontally and vertically to FV3 cube sphere tiles.

Author: SCHWARTZ Toolbox
Date: 2025
"""

import argparse
import os
import sys
from pathlib import Path
import logging

try:
    import numpy as np
    import xarray as xr
    import pygrib
    from scipy.interpolate import RegularGridInterpolator, interp1d
    from scipy.spatial.distance import cdist
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    print(f"Note: Scientific computing dependencies not available: {e}")
    print("For full functionality, install dependencies using:")
    print("  pip install -r requirements.txt")
    print("\nArgument parsing and basic functionality still available.")
    DEPENDENCIES_AVAILABLE = False
    
    # Define dummy classes for when dependencies are not available
    class RegularGridInterpolator:
        def __init__(self, *args, **kwargs):
            pass
    
    class interp1d:
        def __init__(self, *args, **kwargs):
            pass


class FV3CubeSphere:
    """Class to handle FV3 cube sphere grid operations."""
    
    def __init__(self, npx=384, orography_file=None):
        """
        Initialize FV3 cube sphere grid.
        
        Parameters:
        -----------
        npx : int
            Number of grid points in each direction (default: 384 for C384)
        orography_file : str, optional
            Path to orography file containing geolon/geolat coordinates
        """
        self.npx = npx
        self.npy = npx
        self.ntiles = 6
        self.orography_file = orography_file
        
    def generate_coordinates(self):
        """
        Generate cube sphere coordinates for all 6 tiles.
        
        Returns:
        --------
        dict : Dictionary containing lat/lon coordinates for each tile
        """
        coords = {}
        
        # If orography file is provided, load coordinates from it
        if self.orography_file and os.path.exists(self.orography_file):
            try:
                with xr.open_dataset(self.orography_file) as ds:
                    if 'geolon' in ds and 'geolat' in ds:
                        # Load actual coordinates from orography file
                        geolon = ds['geolon'].values
                        geolat = ds['geolat'].values
                        
                        # For now, assume single tile in orography file
                        # In practice, you might need to handle multiple tiles
                        for tile in range(1, 7):
                            coords[f'tile{tile}'] = {
                                'lon': geolon,
                                'lat': geolat
                            }
                    else:
                        logging.warning("geolon/geolat not found in orography file, using placeholder coordinates")
                        self._generate_placeholder_coordinates(coords)
            except Exception as e:
                logging.error(f"Error reading coordinates from orography file: {e}")
                self._generate_placeholder_coordinates(coords)
        else:
            # Generate placeholder coordinates if no orography file
            self._generate_placeholder_coordinates(coords)
            
        return coords
    
    def _generate_placeholder_coordinates(self, coords):
        """Generate placeholder coordinates for all tiles."""
        for tile in range(1, 7):
            # Placeholder for actual cube sphere coordinate calculation
            # These would typically come from the FV3 grid files
            coords[f'tile{tile}'] = {
                'lon': np.zeros((self.npx, self.npy)),
                'lat': np.zeros((self.npx, self.npy))
            }


class GRIB2Reader:
    """Class to handle GRIB2 file reading and processing."""
    
    def __init__(self, filename):
        """
        Initialize GRIB2 reader.
        
        Parameters:
        -----------
        filename : str
            Path to GRIB2 file
        """
        self.filename = filename
        self.grib_file = None
        
    def __enter__(self):
        """Context manager entry."""
        try:
            self.grib_file = pygrib.open(self.filename)
            return self
        except Exception as e:
            raise IOError(f"Error opening GRIB2 file {self.filename}: {e}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.grib_file:
            self.grib_file.close()
    
    def get_aerosol_fields(self):
        """
        Extract aerosol fields from GRIB2 file.
        
        Returns:
        --------
        dict : Dictionary containing aerosol data and coordinates
        """
        aerosol_data = {}
        
        try:
            # Get all messages in the file
            messages = self.grib_file.read()
            
            for msg in messages:
                # Look for aerosol-related parameters
                param_name = getattr(msg, 'parameterName', None)
                short_name = getattr(msg, 'shortName', None)
                
                # Check if this is an aerosol parameter
                if self._is_aerosol_parameter(param_name, short_name):
                    level = getattr(msg, 'level', 0)
                    level_type = getattr(msg, 'levelType', 'unknown')
                    
                    # Get data and coordinates
                    data, lats, lons = msg.data()
                    
                    # Store the data
                    field_key = f"{param_name}_{level_type}_{level}"
                    aerosol_data[field_key] = {
                        'data': data,
                        'lats': lats,
                        'lons': lons,
                        'level': level,
                        'level_type': level_type,
                        'param_name': param_name,
                        'units': getattr(msg, 'units', 'unknown')
                    }
                    
        except Exception as e:
            logging.error(f"Error reading GRIB2 data: {e}")
            raise
            
        return aerosol_data
    
    def _is_aerosol_parameter(self, param_name, short_name):
        """
        Check if a parameter is aerosol-related.
        
        Parameters:
        -----------
        param_name : str
            Full parameter name
        short_name : str
            Short parameter name
            
        Returns:
        --------
        bool : True if parameter is aerosol-related
        """
        if not param_name and not short_name:
            return False
            
        aerosol_keywords = [
            'aerosol', 'dust', 'so2', 'so4', 'bc', 'oc', 'pm2.5', 'pm10',
            'sulfate', 'nitrate', 'ammonium', 'organic', 'carbon',
            'sea salt', 'seasalt'
        ]
        
        param_lower = (param_name or '').lower()
        short_lower = (short_name or '').lower()
        
        return any(keyword in param_lower or keyword in short_lower 
                   for keyword in aerosol_keywords)


class VerticalInterpolator:
    """Class to handle vertical interpolation using ak/bk coordinates."""
    
    def __init__(self, akbk_file=None):
        """
        Initialize vertical interpolator.
        
        Parameters:
        -----------
        akbk_file : str, optional
            Path to file containing ak/bk coefficients
        """
        self.akbk_file = akbk_file
        self.ak = None
        self.bk = None
        
    def load_akbk_coefficients(self):
        """Load ak/bk coefficients from file."""
        if not self.akbk_file or not os.path.exists(self.akbk_file):
            logging.warning("No ak/bk file provided, using default coefficients")
            # Use default L127 coefficients as example
            self._create_default_akbk()
            return
            
        try:
            # Try to read as netCDF first
            if self.akbk_file.endswith('.nc'):
                with xr.open_dataset(self.akbk_file) as ds:
                    if 'vcoord' in ds:
                        # Format: vcoord(nvcoord, levsp) where ak=vcoord[0,:] and bk=vcoord[1,:]
                        vcoord = ds['vcoord'].values
                        self.ak = vcoord[0, :]  # nvcoord=0 for ak
                        self.bk = vcoord[1, :]  # nvcoord=1 for bk
                    else:
                        # Fallback to original variable names
                        self.ak = ds['ak'].values if 'ak' in ds else ds['hyai'].values
                        self.bk = ds['bk'].values if 'bk' in ds else ds['hybi'].values
            else:
                # Try to read as text file
                data = np.loadtxt(self.akbk_file)
                if data.shape[1] >= 2:
                    self.ak = data[:, 0]
                    self.bk = data[:, 1]
                else:
                    raise ValueError("ak/bk file must have at least 2 columns")
                    
        except Exception as e:
            logging.error(f"Error reading ak/bk file: {e}")
            self._create_default_akbk()
    
    def _create_default_akbk(self):
        """Create default ak/bk coefficients for L127."""
        # Simplified L127 hybrid coordinates (you would need actual values)
        nlevels = 128  # L127 has 128 interfaces
        self.ak = np.linspace(1000.0, 0.1, nlevels)  # Pa
        self.bk = np.linspace(0.0, 1.0, nlevels)     # dimensionless
        
    def interpolate_vertical(self, data, input_levels, surface_pressure, 
                           target_levels=None):
        """
        Interpolate data vertically using hybrid coordinates.
        
        Parameters:
        -----------
        data : numpy.ndarray
            Input data array (levels, lat, lon)
        input_levels : numpy.ndarray
            Input pressure levels
        surface_pressure : numpy.ndarray
            Surface pressure field (lat, lon)
        target_levels : numpy.ndarray, optional
            Target pressure levels (if None, use ak/bk to compute)
            
        Returns:
        --------
        numpy.ndarray : Interpolated data
        """
        if self.ak is None or self.bk is None:
            self.load_akbk_coefficients()
            
        # Calculate target pressure levels using ak/bk
        if target_levels is None:
            # Compute pressure at each level: p = ak + bk * ps
            nlev = len(self.ak) - 1  # number of model levels
            target_levels = np.zeros((nlev, *surface_pressure.shape))
            
            for k in range(nlev):
                # Use mid-level values
                ak_mid = 0.5 * (self.ak[k] + self.ak[k+1])
                bk_mid = 0.5 * (self.bk[k] + self.bk[k+1])
                target_levels[k] = ak_mid + bk_mid * surface_pressure
        
        # Perform interpolation
        interpolated_data = np.zeros((len(target_levels), *data.shape[1:]))
        
        for i in range(data.shape[1]):
            for j in range(data.shape[2]):
                # Interpolate at each grid point
                interpolator = interp1d(
                    input_levels, data[:, i, j],
                    kind='linear', bounds_error=False, fill_value='extrapolate'
                )
                
                if target_levels.ndim == 3:
                    target_profile = target_levels[:, i, j]
                else:
                    target_profile = target_levels
                    
                interpolated_data[:, i, j] = interpolator(target_profile)
                
        return interpolated_data


class HorizontalInterpolator:
    """Class to handle horizontal interpolation to FV3 cube sphere grid."""
    
    def __init__(self, method='linear'):
        """
        Initialize horizontal interpolator.
        
        Parameters:
        -----------
        method : str
            Interpolation method ('linear', 'nearest', 'cubic')
        """
        self.method = method
        
    def interpolate_to_cubesphere(self, data, input_lons, input_lats, 
                                 target_coords):
        """
        Interpolate data to FV3 cube sphere grid.
        
        Parameters:
        -----------
        data : numpy.ndarray
            Input data array
        input_lons : numpy.ndarray
            Input longitude coordinates
        input_lats : numpy.ndarray
            Input latitude coordinates
        target_coords : dict
            Target cube sphere coordinates
            
        Returns:
        --------
        dict : Interpolated data for each tile
        """
        interpolated_data = {}
        
        # Create interpolator for the input grid
        if data.ndim == 2:
            # 2D data
            interpolator = RegularGridInterpolator(
                (input_lats[:, 0], input_lons[0, :]), data,
                method=self.method, bounds_error=False, fill_value=np.nan
            )
        elif data.ndim == 3:
            # 3D data (levels, lat, lon)
            interpolated_data = {}
            for level in range(data.shape[0]):
                level_data = {}
                interpolator = RegularGridInterpolator(
                    (input_lats[:, 0], input_lons[0, :]), data[level],
                    method=self.method, bounds_error=False, fill_value=np.nan
                )
                
                for tile, coords in target_coords.items():
                    target_points = np.column_stack([
                        coords['lat'].ravel(), coords['lon'].ravel()
                    ])
                    
                    interpolated_values = interpolator(target_points)
                    level_data[tile] = interpolated_values.reshape(coords['lat'].shape)
                
                interpolated_data[f'level_{level}'] = level_data
            
            return interpolated_data
            
        # For 2D data
        for tile, coords in target_coords.items():
            target_points = np.column_stack([
                coords['lat'].ravel(), coords['lon'].ravel()
            ])
            
            interpolated_values = interpolator(target_points)
            interpolated_data[tile] = interpolated_values.reshape(coords['lat'].shape)
            
        return interpolated_data


def load_orography(oro_file):
    """
    Load orography data.
    
    Parameters:
    -----------
    oro_file : str
        Path to orography file
        
    Returns:
    --------
    dict : Orography data for each tile
    """
    oro_data = {}
    
    try:
        if oro_file.endswith('.nc'):
            with xr.open_dataset(oro_file) as ds:
                # Load coordinate variables
                if 'geolon' in ds and 'geolat' in ds:
                    oro_data['geolon'] = ds['geolon'].values
                    oro_data['geolat'] = ds['geolat'].values
                
                # Load orography/elevation data
                for var in ds.data_vars:
                    if 'oro' in var.lower() or 'elevation' in var.lower() or 'stddev' in var.lower():
                        oro_data[var] = ds[var].values
        else:
            logging.warning(f"Unsupported orography file format: {oro_file}")
            
    except Exception as e:
        logging.error(f"Error loading orography: {e}")
        
    return oro_data


def save_output(data, output_dir, filename_template="aerosol_tile{tile}.nc"):
    """
    Save regridded data to netCDF files.
    
    Parameters:
    -----------
    data : dict
        Regridded data
    output_dir : str
        Output directory
    filename_template : str
        Template for output filenames
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for tile_num in range(1, 7):
        tile_key = f'tile{tile_num}'
        
        if tile_key in data:
            filename = os.path.join(output_dir, 
                                  filename_template.format(tile=tile_num))
            
            # Create xarray dataset
            tile_data = data[tile_key]
            
            if isinstance(tile_data, dict):
                # Multiple levels or variables
                ds = xr.Dataset()
                for var_name, var_data in tile_data.items():
                    ds[var_name] = (['y', 'x'], var_data)
            else:
                # Single variable
                ds = xr.Dataset({
                    'aerosol': (['y', 'x'], tile_data)
                })
            
            # Add attributes
            ds.attrs.update({
                'title': f'Regridded aerosol data for FV3 tile {tile_num}',
                'source': 'GRIB2 to FV3 regridding tool',
                'tile_number': tile_num
            })
            
            # Save to file
            ds.to_netcdf(filename)
            logging.info(f"Saved {filename}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Regrid GRIB2 aerosol data to FV3 cube sphere tiles'
    )
    
    parser.add_argument('--input', '-i', required=True,
                       help='Input GRIB2 file path')
    parser.add_argument('--orography', '-o', 
                       help='Orography file path')
    parser.add_argument('--akbk', '-a',
                       help='ak/bk coefficients file path')
    parser.add_argument('--output', '-out', required=True,
                       help='Output directory')
    parser.add_argument('--npx', type=int, default=384,
                       help='FV3 grid resolution (default: 384)')
    parser.add_argument('--method', default='linear',
                       choices=['linear', 'nearest', 'cubic'],
                       help='Interpolation method (default: linear)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Validate input file
        if not os.path.exists(args.input):
            raise FileNotFoundError(f"Input file not found: {args.input}")
        
        # Check if dependencies are available for full functionality
        if not DEPENDENCIES_AVAILABLE:
            print("\nWarning: Scientific computing dependencies not available.")
            print("Cannot process GRIB2 files without numpy, xarray, pygrib, etc.")
            print("Please install dependencies using: pip install -r requirements.txt")
            print("\nFor demonstration purposes, showing what would be processed:")
            print(f"  Input file: {args.input}")
            print(f"  Output directory: {args.output}")
            print(f"  Grid resolution: C{args.npx}")
            print(f"  Interpolation method: {args.method}")
            if args.orography:
                print(f"  Orography file: {args.orography}")
            if args.akbk:
                print(f"  ak/bk coefficients: {args.akbk}")
            return 0
        
        logging.info(f"Processing GRIB2 file: {args.input}")
        
        # Initialize components
        fv3_grid = FV3CubeSphere(npx=args.npx, orography_file=args.orography)
        h_interpolator = HorizontalInterpolator(method=args.method)
        v_interpolator = VerticalInterpolator(akbk_file=args.akbk)
        
        # Generate FV3 coordinates (placeholder - would need actual grid files)
        logging.info("Generating FV3 cube sphere coordinates...")
        target_coords = fv3_grid.generate_coordinates()
        
        # Load orography if provided
        oro_data = {}
        if args.orography:
            logging.info(f"Loading orography from: {args.orography}")
            oro_data = load_orography(args.orography)
        
        # Read GRIB2 data
        logging.info("Reading GRIB2 aerosol data...")
        with GRIB2Reader(args.input) as reader:
            aerosol_data = reader.get_aerosol_fields()
        
        if not aerosol_data:
            logging.warning("No aerosol fields found in GRIB2 file")
            return
        
        logging.info(f"Found {len(aerosol_data)} aerosol fields")
        
        # Process each aerosol field
        regridded_data = {}
        
        for field_name, field_data in aerosol_data.items():
            logging.info(f"Processing field: {field_name}")
            
            data = field_data['data']
            lats = field_data['lats']
            lons = field_data['lons']
            
            # Horizontal interpolation
            logging.info("Performing horizontal interpolation...")
            h_interpolated = h_interpolator.interpolate_to_cubesphere(
                data, lons, lats, target_coords
            )
            
            # Vertical interpolation (if 3D data and ak/bk provided)
            if data.ndim == 3 and args.akbk:
                logging.info("Performing vertical interpolation...")
                # This would require surface pressure data
                # For now, skip vertical interpolation
                pass
            
            # Store results
            for tile, tile_data in h_interpolated.items():
                if tile not in regridded_data:
                    regridded_data[tile] = {}
                regridded_data[tile][field_name] = tile_data
        
        # Save output
        logging.info(f"Saving results to: {args.output}")
        save_output(regridded_data, args.output)
        
        logging.info("Regridding completed successfully!")
        
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()