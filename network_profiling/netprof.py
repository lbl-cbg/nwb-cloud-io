"""
Example script to test capturing network traffic for remote data reads for NWB

NOTE:  This requires sudo/root access on  macOS and AIX
"""
import tempfile
import signal

from pynwb import NWBHDF5IO
import subprocess
import pyshark
import time
import psutil
from threading import Thread
import os
import numpy as np

# global variables
capture_filename = "tshark_capture.pcap"  # file where the captured packets are stored

class CaptureConnections(Thread):
    """
    Thread class used to  listen for connections on this machine
    and collecting the mapping of connections to process pid's
    """
    def __init__(self):
        super(CaptureConnections, self).__init__()
        self.__connection_to_pid = {}  # map each pair of connection ports to the corresponding process ID (PID)
        self.__run_capture_connections = False  # Used to control the capture_connections thread

    @property
    def connection_to_pid(self):
        return self.__connection_to_pid

    def start(self):
        self.__run_capture_connections = True
        super(CaptureConnections, self).start()

    def stop(self):
        self.__run_capture_connections = False

    def run(self):
        while self.__run_capture_connections:
            # using psutil, we can grab each connection's source and destination ports
            # and their process ID
            for connection in psutil.net_connections():  # NOTE: This requires sudo/root access on  macOS and AIX
                if connection.laddr and connection.raddr and connection.pid:
                    # if local address, remote address and PID are in the connection
                    # add them to our global dictionary
                    self.connection_to_pid[(connection.laddr.port, connection.raddr.port)] = connection.pid
                    self.connection_to_pid[(connection.raddr.port, connection.laddr.port)] = connection.pid
            # check how much sleep-time we should use
            time.sleep(0.2)

class NetProfiler:
    """
    Use TShark command line interface in a subprocess to capture network traffic packets
    in the background.
    """
    def __init__(self, capture_filename=None):
        self.__capture_filename = capture_filename
        self.__tshark_process = None
        self.__capture = None
        self.__packets = None
        if self.__capture_filename is None:
            self.__capture_filename = tempfile.NamedTemporaryFile(mode='w', delete=False)

    def __del__(self):
        self.stop_capture()
        try:
            del self.__capture
        except Exception: # pyshark.capture.capture.TSharkCrashException:
            pass
        #if isinstance(self.__capture_filename, tempfile.NamedTemporaryFile):
        #    self.__capture_filename.close()
        if os.path.exists(self.capture_filename):
            os.remove(self.capture_filename)

    @property
    def packets(self):
        if self.__packets is None:
            try:
                cap = pyshark.FileCapture(capture_filename)
                self.__packets = [packet for packet in cap]
                del cap
            except:
                pass
        return self.__packets
    @property
    def capture_filename(self):
        if isinstance(self.__capture_filename, str):
            return self.__capture_filename
        else:
            return self.__capture_filename.name

    @property
    def capture(self):
        return self.__capture

    def start_capture(self):
        tsharkCall = ["tshark", "-w", capture_filename]
        self.__tshark_process = subprocess.Popen(tsharkCall, stderr=subprocess.DEVNULL) #,
                                                 # stdout=subprocess.PIPE, shell=True,
                                                 # start_new_session=True)#,
                                                # preexec_fn=os.setsid)
        time.sleep(0.2)  # not sure if this is needed but just to be safe

    def stop_capture(self):
        if self.__tshark_process is not None:
            self.__tshark_process.terminate()
            self.__tshark_process.kill()
            del self.__tshark_process
            self.__tshark_process = None

    def get_packets_for_connections(self, pid_connections: list):
        pid_packets = []
        try:
            for packet in self.packets:
                if hasattr(packet, 'tcp'):
                    ports = int(str(packet.tcp.srcport)), int(str(packet.tcp.dstport))
                    if ports in pid_connections:
                        pid_packets.append(packet)
        except Exception:  # pyshark.capture.capture.TSharkCrashException:
            pass
        return pid_packets



def size_to_str(bytes: int) -> str:
    """
    Format the size in bytes as a human-readable string
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024


if __name__ == "__main__":

    ###
    # This would be part of the setUp() of a test
    ##
    # start the capture_connections() function to update the current connections of this machine
    connections_thread = CaptureConnections()
    connections_thread.start()
    time.sleep(0.2) # not sure if this is needed but just to be safe

    # start capturing the raw packets by running the tshark commandline tool in a subprocess
    netprofiler = NetProfiler()
    netprofiler.start_capture()

    ###
    # This would be the unit test
    ###
    # Read the NWB data file from DANDI
    s3_path = 'https://dandiarchive.s3.amazonaws.com/ros3test.nwb'
    with NWBHDF5IO(s3_path, mode='r', driver='ros3') as io:
        nwbfile = io.read()
        test_data = nwbfile.acquisition['ts_name'].data[:]

    ###
    # This part would go into tearDown to stop the capture and compute statistics
    ###
    # Stop capturing packets and connections
    netprofiler.stop_capture()
    connections_thread.stop()

    # get the connections for the PID of this process
    pid_connections =  [k for k, v in connections_thread.connection_to_pid.items() if v == os.getpid()]

    # Parse packets and filter out all the packets for this process pid by matching with the pid_connections
    pid_packets = netprofiler.get_packets_for_connections(pid_connections)

    # Print basic connection statistics
    print("Number of connections:", int(len(pid_connections) / 2.0))
    print("Number of packets: ", len(pid_packets))
    print("Bytes transferred:", size_to_str(np.sum([len(packet) for packet in pid_packets])))
