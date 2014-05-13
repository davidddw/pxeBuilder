#!/usr/bin/env python
# encoding: utf-8

import sys
import pxe
from pxe_data import mac

def main(ip):
    pxe.setup_esxi_pxe('pxe.cfg', mac[ip], 'esxi55', '172.16.1.'+ip, 'esxi'+ip)

if __name__ == "__main__":
    main(sys.argv[1])