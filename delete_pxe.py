#!/usr/bin/env python
# encoding: utf-8

import sys
import pxe
from pxe_data import mac

def main(ip, mtype):
    mac_name = '01-'+'-'.join(mac[ip].lower().split(":"))
    pxe.delete_pxe('pxe.cfg', mac_name, mtype)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])