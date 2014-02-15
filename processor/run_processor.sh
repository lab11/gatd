#!/bin/bash

screen -S gatd-processor -d -m ./processor.py monjolo_freq
screen -S gatd-processor -d -m ./processor.py monjolo_ground_truth
screen -S gatd-processor -d -m ./processor.py wattsup_aggregate
