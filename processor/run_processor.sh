#!/bin/bash

screen -S gatd-processor-monjolo-freq -d -m ./processor.py monjolo_freq
screen -S gatd-processor-monjolo-gt   -d -m ./processor.py monjolo_ground_truth
screen -S gatd-processor-wattsup-agg  -d -m ./processor.py wattsup_aggregate
