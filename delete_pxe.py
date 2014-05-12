#!/usr/bin/env python
# encoding: utf-8

import sys
import pxe
from pxe_data import mac

def main(ip):
    mac_name = '01-'+'-'.join(mac[ip].lower().split(":"))
    pxe.delete_xen_pxe('pxe.cfg', mac_name)

if __name__ == "__main__":
    main(sys.argv[1])