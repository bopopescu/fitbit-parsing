#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Find best performance efforts for different channels for different ranges of time.

Each entry in the Fit File are one second apart. So we don't need to know the timestamps for the entries.
Rather, we can store the entries in an array then find the maximum average for specified ranges based on
how many seconds are in the minute range.
"""
__author__ = "Ben Pingilley"
__email__ = "ben.pingilley@gmail.com"

import sys
from fitparse import FitFile
import multiprocessing as mp

if len(sys.argv) < 2:
    print("Usage: python %s <filename>" % sys.argv[0])
    sys.exit(1)

def get_best_avg(l, c, i, s, q):
    '''
    Get best average of the list (l) based on the range (s)
    Args:
        l (list): List of all values for specific channel.
        c (str): Channel name (power, speed, or heart rate).
        i (int): Index of results dictionary to add data.
        s (int): Number of seconds in range.
        q (class): Queue for parallel process.
    '''
    # Initialize best result (b) as zero
    b = 0

    # Iterate through array
    for x in range(0, len(l)-s):
        # Compare the current best average to the average of the new range
        b = max(sum(l[x:x+s])/s, b)

    # Push best to queue
    q.put((b, c, i))

def parallel(d):
    '''
    Use multiprocessing module to setup parellel processing of each channel and range
    Args:
        d (dict): Channel dictionary with a nested list of best efforts and a list of all the channels values.
    '''

    # Define a process output queue
    output = mp.Queue()

    # Initialize a list for parallel processes that we want to run
    processes = []

    # Channels
    for channel in d.keys():
        # Minute ranges
        for idx, min_range in enumerate([60, 300, 600, 900, 1200]):
            # Add processes to list. 
            processes.append(mp.Process(target=get_best_avg, args=(d[channel][5], channel, idx, min_range, output)))

    # Run processes
    for proc in processes:
        proc.start()

    # Exit the completed processes
    for proc in processes:
        proc.join()

    # Get process results from the output queue
    for proc in processes:
        # Split output queue results into varibales
        val, channel, idx = output.get()
        # Assign value to specified channel and minute range in dictionary
        d[channel][idx] = val

    # Prints reults after all processes have completed
    print_results(d)

def print_results(d):
    '''
    Print Results from parallel processing
    Args:
        d (dict): Channel dictionary with a nested list of best efforts and a list of all the channels values.
    '''

    print ( "Best Continuous per Minute Range\n\n   Power (watts):\n\t 1 : %s\n\t 5 : %s\n\t10 : %s\n\t15 : %s\n\t20 : %s\
    \n\n   Speed (m/s):\n\t 1 : %s\n\t 5 : %s\n\t10 : %s\n\t15 : %s\n\t20 : %s\
    \n\n   Heart Rate (bpm):\n\t 1 : %s\n\t 5 : %s\n\t10 : %s\n\t15 : %s\n\t20 : %s") % (
        d['power'][0], d['power'][1], d['power'][2], d['power'][3], d['power'][4],
        d['speed'][0], d['speed'][1], d['speed'][2], d['speed'][3], d['speed'][4],
        d['heart_rate'][0], d['heart_rate'][1], d['heart_rate'][2], d['heart_rate'][3], d['heart_rate'][4]
    )

def main():
    '''Open Fit File and create lists of values depending on channel'''

    # Channel dictionary with a nested list of best efforts and a list of all the channels values.
    # [0] = 1 Minute
    # [1] = 5 Minutes
    # [2] = 10 Minutes
    # [3] = 15 Minutes
    # [4] = 20 Minutes
    d = {'power': [0, 0, 0, 0, 0, []], 
         'speed': [0, 0, 0, 0, 0, []], 
         'heart_rate': [0, 0, 0, 0, 0, []]}

    # Open and parse Fit File from user input
    with open(sys.argv[1], 'rb') as f:
        fitfile = FitFile(f)
        # Get all data messages that are of type record
        for r in fitfile.get_messages('record'):
            # For each record, find those with a name in our dictionary
            for k in d.keys():
                v = r.get_value(k)
                # Some values are set to None. Need to convert them to integers
                if v is None: v = 0
                # Append value in list of specified by dictionary key
                d[k][5].append(v)

    # Start processing of different ranges using parallel processing
    parallel(d)

if __name__ == "__main__":
    main()