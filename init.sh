#!/bin/sh
export license_key='5o8Y4YPrNFovbsNLaiA9zaE18kgrPgzf'
cd /home/linaro/probe; nohup python main.py &
nohup /usr/local/bin/iperf -s &
nohup /usr/local/bin/iperf -s -u &

sudo apt-get -y remove ubuntu-release-upgrader-core

