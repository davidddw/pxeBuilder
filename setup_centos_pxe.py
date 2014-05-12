#!/usr/bin/env python
# encoding: utf-8

import sys
import pxe
from pxe_data import mac

def main(ip):
    mac_name = '01-'+'-'.join(mac[ip].lower().split(":"))
    pxe.setup_centos_pxe('pxe.cfg', mac_name, 'centos', '172.16.1.'+ip, 'centos'+ip)

if __name__ == "__main__":
    main('130')