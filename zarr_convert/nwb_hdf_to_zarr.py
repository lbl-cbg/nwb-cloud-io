from pynwb import NWBHDF5IO
from hdmf_zarr.nwb import NWBZarrIO
import sys

def print_help():
    print("The script requires exactly one arguments. Call with")
    print("python nwb_hdf_to_zarr.py <hdf5_filename>")
    print("")
    print("The output zarr file will be named the same as the HDF5 file with the added .zarr extension")

def convert(hdf_filename: str, zarr_filename: str):
    with NWBHDF5IO(hdf_filename, 'r', load_namespaces=True) as read_io:  # Create HDF5 IO object for read
        with NWBZarrIO(zarr_filename, mode='w') as export_io:         # Create Zarr IO object for write
            export_io.export(src_io=read_io, write_args=dict(link_data=False))   # Export from HDF5 to Zarr

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print_help()
        exit(0)
    else:
        hdf_filename = sys.argv[1]
        zarr_filename = hdf_filename +".zarr"
        convert(hdf_filename=hdf_filename, zarr_filename=zarr_filename)






