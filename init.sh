#!/bin/sh

cd /home/linaro/probe; nohup python main.py &
nohup /usr/local/bin/iperf -s &
nohup /usr/local/bin/iperf -s -u &

sudo apt-get -y remove ubuntu-release-upgrader-core

