"""
Convert an NWB HDF5 file to Zarr
"""

from pynwb import NWBHDF5IO
from hdmf_zarr.nwb import NWBZarrIO
import sys
from zarr.storage import (DirectoryStore,
                          NestedDirectoryStore)


def print_help():
    print("The script requires exactly one arguments. Call with")
    print("python nwb_hdf_to_zarr.py <>store> <hdf5_filename>")
    print("")
    print("The output file will be named according to the HDF5 file with a new .zarr extension")
    print("The store parameter is optional. One of: NestedDirectoryStore or DirectoryStore.")


def convert(hdf_filename: str,
            zarr_filename: str):
    with NWBHDF5IO(hdf_filename, 'r', load_namespaces=True) as read_io:  # Create HDF5 IO object for read
        with NWBZarrIO(zarr_filename, mode='w') as export_io:         # Create Zarr IO object for write
            export_io.export(src_io=read_io, write_args=dict(link_data=False))   # Export from HDF5 to Zarr


if __name__ == "__main__":
    if len(sys.argv) == 2:
        hdf_filename = sys.argv[1]
        zarr_filename = hdf_filename + ".zarr"
        convert(hdf_filename=hdf_filename,
                zarr_filename=zarr_filename)
    elif len(sys.argv) == 3:
        store = sys.argv[1]
        hdf_filename = sys.argv[2]
        zarr_filename = hdf_filename.rstrip(".nwb") + "_" + store + "_" + "nwb.zarr"
        if store == "NestedDirectoryStore":
            zarr_store = NestedDirectoryStore(zarr_filename)
        elif store == "DirectoryStore":
            zarr_store = DirectoryStore(zarr_filename)
        else:
            raise ValueError("Bad 'store' parameter. Got %s expected on off NestedDirectoryStore, DirectoryStore " % store)
        convert(hdf_filename=hdf_filename,
                zarr_filename=zarr_store)
    else:
        print_help()
        exit(0)
