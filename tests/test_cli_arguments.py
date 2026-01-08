"""Test CLI argument parsing functionality of main.py"""

import os
import tempfile
import pytest
import argparse
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

from main import main, transform_route_info_from_gpx_file


def test_cli_transform_command_with_all_parameters():
    """Test all parameters for transform command"""
    # Create temporary GPX input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg><trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2023-01-01T10:00:00Z</time></trkpt></trkseg></trk></gpx>')
        temp_input_path = temp_input.name

    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    # Mock dependency function to avoid actual processing
    with patch('main.transform_route_info_from_gpx_file') as mock_transform:
        # Simulate command line arguments
        sys.argv = [
            'main.py', 'transform',
            temp_input_path,
            temp_output_gpx,
            temp_output_csv,
            '--coordinate_type', 'wgs84',
            '--transformed_coordinate_type', 'gcj02',
            '--area_source', 'gdf',
            '--map_api_ak', 'mock_api_key',
            '--map_freq', '5',
            '--baidu_get_en_result', 'True'
        ]

        try:
            main()
            # Verify function was called correctly
            mock_transform.assert_called_once()
            # Verify call arguments
            call_args = mock_transform.call_args
            assert call_args.kwargs['coordinate_type'] == 'wgs84'
            assert call_args.kwargs['transformed_coordinate_type'] == 'gcj02'
            assert call_args.kwargs['source'] == 'gdf'
            assert call_args.kwargs['map_api_ak'] == 'mock_api_key'
            assert call_args.kwargs['map_freq'] == 5
            assert call_args.kwargs['baidu_get_en_result'] is True
        except SystemExit:
            # Expected exit behavior
            pass
        finally:
            # Clean up temporary files
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)


def test_cli_transform_command_no_transform():
    """Test transform command with disabled coordinate transformation"""
    # Create temporary GPX input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg><trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2023-01-01T10:00:00Z</time></trkpt></trkseg></trk></gpx>')
        temp_input_path = temp_input.name

    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    # Mock dependency function to avoid actual processing
    with patch('main.transform_route_info_from_gpx_file') as mock_transform:
        # Simulate command line arguments
        sys.argv = [
            'main.py', 'transform',
            temp_input_path,
            temp_output_gpx,
            temp_output_csv,
            '--no_transform_coordinate',
            '--no_set_area'
        ]

        try:
            main()
            # Verify function was called correctly
            mock_transform.assert_called_once()
            # Verify call arguments
            call_args = mock_transform.call_args
            assert call_args.kwargs['transform_coordinate'] is False
            assert call_args.kwargs['set_area'] is False
        except SystemExit:
            # Expected exit behavior
            pass
        finally:
            # Clean up temporary files
            if os.path.exists(temp_input_path):
                os.remove(temp_input_path)


def test_cli_area_source_validation():
    """Test valid options for area_source parameter"""
    # Create temporary GPX input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg><trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2023-01-01T10:00:00Z</time></trkpt></trkseg></trk></gpx>')
        temp_input_path = temp_input.name

    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    # Test valid area_source options
    valid_sources = ['nominatim', 'gdf', 'baidu', 'amap']
    
    for source in valid_sources:
        with patch('main.transform_route_info_from_gpx_file') as mock_transform:
            sys.argv = [
                'main.py', 'transform',
                temp_input_path,
                temp_output_gpx,
                temp_output_csv,
                '--area_source', source
            ]
            
            try:
                main()
                # Verify function was called
                call_args = mock_transform.call_args
                assert call_args.kwargs['source'] == source
            except SystemExit:
                pass
    
    # Clean up temporary file
    if os.path.exists(temp_input_path):
        os.remove(temp_input_path)


def test_cli_output_paths_generation():
    """Test auto-generation of output paths when not provided"""
    # Create temporary GPX input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg><trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2023-01-01T10:00:00Z</time></trkpt></trkseg></trk></gpx>')
        temp_input_path = temp_input.name

    # Mock dependency function
    with patch('main.transform_route_info_from_gpx_file') as mock_transform:
        sys.argv = [
            'main.py', 'transform',
            temp_input_path  # Only provide input, no output paths
        ]
        
        try:
            main()
            # Verify function was called with auto-generated output paths
            mock_transform.assert_called_once()
            call_args = mock_transform.call_args
            # Verify output paths are based on input filename
            assert temp_input_path.replace('.gpx', '-transformed.gpx') == call_args.args[1]  # output_gpx
            assert temp_input_path.replace('.gpx', '.csv') == call_args.args[2]  # output_csv
        except SystemExit:
            pass
    
    # Clean up temporary file
    if os.path.exists(temp_input_path):
        os.remove(temp_input_path)


def test_cli_invalid_area_source_fails():
    """Test that invalid area_source parameter causes an error"""
    # Create temporary GPX input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gpx', delete=False) as temp_input:
        temp_input.write('<?xml version="1.0" encoding="UTF-8"?><gpx version="1.1"><trk><trkseg><trkpt lat="39.9042" lon="116.4074"><ele>50.0</ele><time>2023-01-01T10:00:00Z</time></trkpt></trkseg></trk></gpx>')
        temp_input_path = temp_input.name

    temp_output_gpx = tempfile.mktemp(suffix='.gpx')
    temp_output_csv = tempfile.mktemp(suffix='.csv')

    try:
        # Capture stderr to verify error message
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            sys.argv = [
                'main.py', 'transform',
                temp_input_path,
                temp_output_gpx,
                temp_output_csv,
                '--area_source', 'invalid_source'
            ]
            
            with pytest.raises(SystemExit):
                main()
            
            # Verify error message contains invalid parameter info
            error_output = mock_stderr.getvalue()
            assert "error" in error_output.lower() or "invalid" in error_output.lower()
    finally:
        # Clean up temporary file
        if os.path.exists(temp_input_path):
            os.remove(temp_input_path)