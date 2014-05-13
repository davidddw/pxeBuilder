#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import ConfigParser 
from string import Template 

from optparse import OptionParser

def get_real_path():
    current_path = os.path.dirname(os.path.realpath(__file__))
    return current_path

def check_src_dir_exist(folder):
    real_path = os.path.join(get_real_path(), folder)
    if not os.path.exists(real_path):
        os.makedirs(real_path)
    return real_path

def check_dest_dir_exist(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path

def delete_dir_exist(folder):
    real_path = os.path.join(get_real_path(), folder)
    if os.path.exists(real_path):
        os.rmdir(real_path)

def get_config_from_cfg(config_file, section):
    filename = os.path.join(check_src_dir_exist('conf'), config_file)
    cf = ConfigParser.ConfigParser()    
    cf.read(filename)
    return dict(cf.items(section))
    
def generate_file_from_temp(srcdir,srcfile, destdir, destfile, **karg):
    srcfilename = os.path.join(check_src_dir_exist(srcdir), srcfile)
    destfilename = os.path.join(check_dest_dir_exist(destdir), destfile)
    with open(srcfilename, "r") as f:
        content = Template(f.read())
    with open(destfilename, "w") as f:
        f.write(content.substitute(**karg))
        
def setup_xen_pxe(filename, mac, m_type, ipaddr, hostname):
    gl_config = get_config_from_cfg(filename, 'global')
    mac_name = '01-'+'-'.join(mac.lower().split(":"))
    answer = mac_name+'.xml'
    config = get_config_from_cfg(filename, m_type)
    config.update({'answerfile':answer})
    config.update({'xen_ipaddr':ipaddr})
    config.update({'xen_hostname':hostname})
    config.update(**gl_config)
    generate_file_from_temp(gl_config['temp_folder'], 'xen_pxe.in', 
                            gl_config['pxelinux'], mac_name, **config)
    print("Info: generate %s in %s" % (mac_name, gl_config['pxelinux']))
    generate_file_from_temp(gl_config['temp_folder'], m_type+'.in', 
                            gl_config['nfs_ans'], answer, **config)
    print("Info: generate %s in %s" % (answer, gl_config['nfs_ans']))
    
def setup_centos_pxe(filename, mac, m_type, ipaddr, hostname):
    gl_config = get_config_from_cfg(filename, 'global')
    mac_name = '01-'+'-'.join(mac.lower().split(":"))
    answer = mac_name+'.ks'
    config = get_config_from_cfg(filename, m_type)
    config.update(**gl_config)
    config.update({'answerfile':answer})
    config.update({'host_ipaddr':ipaddr})
    config.update({'hostname':hostname})
    generate_file_from_temp(gl_config['temp_folder'],  m_type+'_pxe.in', 
                            gl_config['pxelinux'], mac_name, **config)
    print("Info: generate %s in %s" % (mac_name, gl_config['pxelinux']))
    generate_file_from_temp(gl_config['temp_folder'], m_type + '.in', 
                            gl_config['nfs_ans'], answer, **config)
    print("Info: generate %s in %s" % (answer, gl_config['nfs_ans']))
    
def setup_esxi_pxe(filename, mac, m_type, ipaddr, hostname):
    gl_config = get_config_from_cfg(filename, 'global')
    mac_name = '01-'+'-'.join(mac.lower().split(":"))
    answer = mac_name +'.ks'
    config = get_config_from_cfg(filename, m_type)
    config.update(**gl_config)
    config.update({'ksfile':answer})
    config.update({'macaddr':mac})
    config.update({'host_ipaddr':ipaddr})
    config.update({'hostname':hostname})
    generate_file_from_temp(gl_config['temp_folder'],  m_type+'_pxe.in', 
                            gl_config['pxelinux'], mac_name, **config)
    print("Info: generate %s in %s" % (mac_name, gl_config['pxelinux']))
    generate_file_from_temp(gl_config['temp_folder'], m_type + '.in', 
                            gl_config['nfs_ans'], answer, **config)
    print("Info: generate ks: %s in %s" % (answer, gl_config['nfs_ans']))
    
def delete_pxe(filename, mac, m_type):
    gl_config = get_config_from_cfg(filename, 'global')
    mac_name = '01-'+'-'.join(mac.lower().split(":"))
    if m_type=='xenserver' or m_type=='xcp':
        answer = mac_name+'.xml'
    else:
        answer = mac_name+'.ks'
    mac_file = os.path.join(gl_config['pxelinux'], mac_name)
    answer_file = os.path.join(gl_config['nfs_ans'], answer)
    if os.path.isfile(mac_file):
        os.remove(mac_file)
        print("Info: remove %s" % mac_file)
    else:
        print("Info: %s not exist" % mac_file)
    if os.path.isfile(answer_file):
        os.remove(answer_file)
        print("Info: remove %s" % answer_file)
    else:
        print("Info: %s not exist" % answer_file)
        
def main(argv=None):
    program_name = os.path.basename(sys.argv[0])
    program_version = "v0.1"
    if argv is None:
        argv = sys.argv[1:]
    try:
        # setup option parser
        usage = "usage: %prog [options] arg1 arg2"
        parser = OptionParser(usage=usage, version=program_version)
        parser.add_option("-f", "--file", default="pxe.cfg", help="set config file [default: %default]")
        parser.add_option("-t", "--type", dest="type", help="set type")
        parser.add_option("-i", "--ip", dest="ipaddr", help="set ipaddress")
        parser.add_option("-n", "--hostname", dest="hostname", help="set hostname")
        parser.add_option("-m", "--mac", dest="mac", help="set mac address")
        # process options
        (opts, args) = parser.parse_args(argv)
        if opts.mac is None:
            parser.print_help()
            sys.exit()
        else:
            mac = '01-'+'-'.join(opts.mac.lower().split(":"))
        if opts.ip is None:
            parser.print_help()
            sys.exit()
        if opts.hostname is None:
            parser.print_help()
            sys.exit()
        if opts.type is None:
            parser.print_help()
            sys.exit()
        else:
            setup_xen_pxe(opts.file, mac, opts.type, opts.ip, opts.hostname)

    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2
    
if __name__ == "__main__":
    main()
