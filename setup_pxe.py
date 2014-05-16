#!/usr/bin/env python
# encoding: utf-8

import sys
from pxe_data import mac 
from pxe import PXE


def run(ip_end, m_type):
    pxe = PXE('pxe.cfg', mac[ip_end])
    ip = '172.16.1.%s' % ip_end
    if m_type=='xenserver' or m_type=='xcp':
        pxe.setup_xen_pxe(ip, m_type+ip_end, m_type)
    elif m_type=='centos':
        pxe.setup_centos_pxe(ip, m_type+ip_end)
    elif m_type=='esxi':
        pxe.setup_esxi_pxe(ip, m_type+ip_end)
    elif m_type=='dhcp':
        pxe.generate_dhcp_http_pxe()
        
if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])