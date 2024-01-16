#!/bin/bash

# activate the python env
module load conda
conda activate nwb_zarr

# Download the file
if ! test -f sub-npI3_ses-20190421_behavior+ecephys.nwb; then
	wget https://api.dandiarchive.org/api/assets/ac03f90d-746b-48b1-8c12-0416fdaa79cc/download/
fi
if ! test -f sub-R6_ses-20200206T210000_behavior+ophys.nwb; then
	wget https://api.dandiarchive.org/api/assets/11ef11cc-130b-4d22-8af0-aa4798c64584/download/
fi
if ! test -f sub-1214579789_ses-1214621812_icephys.nwb; then
	wget https://api.dandiarchive.org/api/assets/1142cd85-96f9-4ae2-9d71-f722887fb3c0/download/
fi

# Convert the files
if ! test -f sub-npI3_ses-20190421_behavior+ecephys.nwb.zarr; then
	python nwb_hdf_to_zarr.py sub-npI3_ses-20190421_behavior+ecephys.nwb
fi

if ! test -f sub-R6_ses-20200206T210000_behavior+ophys.nwb.zarr; then
        python nwb_hdf_to_zarr.py sub-R6_ses-20200206T210000_behavior+ophys.nwb
fi

if ! test -f sub-1214579789_ses-1214621812_icephys.nwb.zarr; then
        python nwb_hdf_to_zarr.py sub-1214579789_ses-1214621812_icephys.nwb
fi

