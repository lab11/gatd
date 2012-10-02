#!/bin/bash


PORT=19000

screen -S mongodb -d -m mongod --port $PORT


