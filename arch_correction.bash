#!/bin/bash
echo "/usr/lib64" | sudo tee /etc/ld.so.conf.d/modal_pipe.conf
sudo ldconfig
