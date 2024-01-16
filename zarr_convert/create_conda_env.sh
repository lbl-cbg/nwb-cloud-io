#!/bin/bash

module load conda
conda create --name nwb_zarr python=3.11
conda activate nwb_zarr
conda install h5py
pip install dandi

git clone --recurse-submodules https://github.com/hdmf-dev/hdmf.git
cd hdmf
pip install -r requirements.txt -r requirements-dev.txt -r requirements-doc.txt -r requirements-opt.txt
pip install -e .
cd ..

git clone https://github.com/hdmf-dev/hdmf-zarr.git
cd hdmf-zarr
pip install -r requirements.txt -r requirements-dev.txt -r requirements-doc.txt
pip install -e .


