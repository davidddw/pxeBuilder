#!/usr/bin/env python
# encoding: utf-8

import sys
import pxe
from pxe_data import mac

def main(ip):
    pxe.setup_centos_pxe('pxe.cfg', mac[ip], 'centos', '172.16.1.'+ip, 'centos'+ip)

if __name__ == "__main__":
    main(sys.argv[1])