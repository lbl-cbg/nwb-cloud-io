"""
Example script to test capturing network traffic for remote data reads for NWB

NOTE:  This requires sudo/root access on  macOS and AIX
"""
from pynwb import NWBHDF5IO
import subprocess
import pyshark
import time
import psutil
from threading import Thread
import os
import numpy as np

# global variables
run_capture_connections = True  # Used to control the capture_connections thread
connection_to_pid = {}  # map each pair of connection ports to the corresponding process ID (PID)
capture_filename = "tshark_capture.pcap"  # file where the captured packets are stored

def capture_connections():
    """
    Use psutil to listen for connections on this machine
    and adds them to `connection_to_pid` global variable

    NOTE: This requires sudo/root access on  macOS and AIX
    """
    global run_capture_connections
    global connection_to_pid
    while run_capture_connections:
        # using psutil, we can grab each connection's source and destination ports
        # and their process ID
        for connection in psutil.net_connections():  # NOTE: This requires sudo/root access on  macOS and AIX
            if connection.laddr and connection.raddr and connection.pid:
                # if local address, remote address and PID are in the connection
                # add them to our global dictionary
                connection_to_pid[(connection.laddr.port, connection.raddr.port)] = connection.pid
                connection_to_pid[(connection.raddr.port, connection.laddr.port)] = connection.pid
        # check how much sleep-time we should use
        time.sleep(0.2)

def size_to_str(bytes: int) -> str:
    """
    Format the size in bytes as a human-readable string
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

# start the capture_connections() function to update the current connections of this machine
connections_thread = Thread(target=capture_connections)
connections_thread.start()
time.sleep(0.2) # not sure if this is needed but just to be safe

# start capturing the raw packets by running the tshark commandline tool in a subprocess
# tsharkCall = ["tshark", "-i", "en0", "-w", capture_filename]
tsharkCall = ["tshark", "-w", capture_filename]
print("Starting TShark")
tshark_process = subprocess.Popen(tsharkCall, stderr=subprocess.DEVNULL)
time.sleep(0.2) # not sure if this is needed but just to be safe

# Read the NWB data file from DANDI
s3_path = 'https://dandiarchive.s3.amazonaws.com/ros3test.nwb'
with NWBHDF5IO(s3_path, mode='r', driver='ros3') as io:
    nwbfile = io.read()
    test_data = nwbfile.acquisition['ts_name'].data[:]

# Stop capturing packets and connections
tshark_process.kill()
run_capture_connections = False

# parse the captured packets
cap = pyshark.FileCapture(capture_filename)

# get the connections for the PID of this process
pid_connections =  [k for k, v in connection_to_pid.items() if v == os.getpid()]

# Filter out all the packets for this process pid by matching with the pid_connections
pid_packets = []
try:
    for packet in cap:
        if hasattr(packet, 'tcp'):
            ports = int(str(packet.tcp.srcport)), int(str(packet.tcp.dstport))
            if ports in pid_connections:
                pid_packets.append(packet)
except Exception: # pyshark.capture.capture.TSharkCrashException:
    pass
# Print basic connection statistics
print("Number of connections:", int(len(pid_connections) / 2.0))
print("Number of packets: ", len(pid_packets))
print("Bytes transferred:", size_to_str(np.sum([len(packet) for packet in pid_packets])))
