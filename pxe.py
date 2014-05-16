#!/usr/bin/env python
# encoding: utf-8

import sys
import os
import ConfigParser 
from string import Template
from pxe_data import mac 

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

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
        
class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg
        
class PXE():
    def __init__(self, filename, mac):
        self.gl_config = get_config_from_cfg(filename, 'global')
        self.mac_name = '01-%s' % '-'.join(mac.lower().split(":"))
        self.mac = mac
        self.filename = filename
        self.tftpboot = os.path.join(os.getcwd(),self.gl_config['tftp_root'], 
                                     'pxelinux.cfg')
        self.answer_path = os.path.join(os.getcwd(),self.gl_config['www_root'], 
                                    self.gl_config['kick_url'])
        self.temp = self.gl_config['temp_folder']
        
    def setup_xen_pxe(self, ipaddr, hostname, m_type='xenserver'):
        answer = self.mac_name+'.xml'
        config = get_config_from_cfg(self.filename, m_type)
        config.update({'answerfile':answer})
        config.update({'xen_ipaddr':ipaddr})
        config.update({'xen_hostname':hostname})
        config.update(**self.gl_config)
        
        generate_file_from_temp(self.temp, 'xen_pxe.in', self.tftpboot, 
                                self.mac_name, **config)
        print("Info: generate %s in %s" % (self.mac_name, self.tftpboot))
        generate_file_from_temp(self.temp, m_type+'.in', 
                                self.answer_path, answer, **config)
        print("Info: generate %s in %s" % (answer, self.answer_path))
    
    def setup_centos_pxe(self, ipaddr, hostname, m_type='centos'):
        answer = self.mac_name+'.ks'
        config = get_config_from_cfg(self.filename, m_type)
        config.update({'answerfile':answer})
        config.update({'host_ipaddr':ipaddr})
        config.update({'hostname':hostname})
        config.update(**self.gl_config)

        generate_file_from_temp(self.temp,  m_type+'_pxe.in', 
                                self.tftpboot, self.mac_name, **config)
        print("Info: generate %s in %s" % (self.mac_name, self.tftpboot))
        generate_file_from_temp(self.temp, m_type + '.in', 
                                self.answer_path, answer, **config)
        print("Info: generate %s in %s" % (answer, self.answer_path))
    
    def setup_esxi_pxe(self, ipaddr, hostname, m_type='esxi55'):
        answer = '%s.ks' % self.mac_name
        cfgfile = '%s.cfg' % self.mac_name
        config = get_config_from_cfg(self.filename, m_type)
        config.update(**self.gl_config)
        config.update({'ksfile':answer})
        config.update({'cfgfile':cfgfile})
        config.update({'macaddr':self.mac})
        config.update({'host_ipaddr':ipaddr})
        config.update({'hostname':hostname})

        generate_file_from_temp(self.temp, m_type+'_pxe.in', 
                                self.tftpboot, self.mac_name, **config)
        print("Info: generate %s in %s" % (self.mac_name, self.tftpboot))
        generate_file_from_temp(self.temp, m_type + '_cfg.in', 
                                self.answer_path, cfgfile, **config)
        print("Info: generate ks: %s in %s" % (cfgfile, self.answer_path))
        generate_file_from_temp(self.temp, m_type + '.in', 
                                self.answer_path, answer, **config)
        print("Info: generate ks: %s in %s" % (answer, self.answer_path))
        
    def generate_dhcp_pxe(self, dhcp_name='dhcp'):
        dhcp_config = get_config_from_cfg(self.filename, 'dhcp')
        dhcp_config.update(**self.gl_config)
        myhostString = ""
        for (k,v) in mac.items():
            if v != '':
                myhostString +='dhcp-host=net:%slinux,%s,%s\n' \
                    % (dhcp_config['pxe_method'], v, '172.16.1.'+ k )
        dhcp_config.update({'dhcp_hosts':myhostString, 'tftp_root': self.tftpboot})
        generate_file_from_temp(self.temp, 'dhcp.in', 
                                dhcp_config['dnsmasq_path'], dhcp_name, **dhcp_config)
        print("Info: generate dhcp: %s in %s" % (dhcp_name, dhcp_config['dnsmasq_path']))
        wwwroot = os.path.join(os.getcwd(),self.gl_config['www_root'])
        dhcp_config.update({'wwwroot':wwwroot})
        generate_file_from_temp(self.temp, 'lighttpd.in', 
                                dhcp_config['lighttpd_path'], 'lighttpd.conf', **dhcp_config)
        print("Info: generate lighttpd: %s in %s" % ('lighttpd.conf', dhcp_config['lighttpd_path'])) 
    
    def delete_pxe(self, m_type):
        if m_type=='xenserver' or m_type=='xcp':
            answer = '%s.xml' % self.mac_name
        else:
            answer = '%s.ks' % self.mac_name
        mac_file = os.path.join(self.tftpboot, self.mac_name)
        if os.path.isfile(mac_file):
            os.remove(mac_file)
            print("Info: remove %s" % mac_file)
        else:
            print("Info: %s not exist" % mac_file)
        answer_file = os.path.join(self.answer_path, answer)
        if os.path.isfile(answer_file):
            os.remove(answer_file)
            print("Info: remove %s" % answer_file)
        else:
            print("Info: %s not exist" % answer_file)
        if m_type=='esxi':
            cfg_file = '%s.cfg' % self.mac_name
            cfg_file = os.path.join(self.answer_path, cfg_file)
            if os.path.isfile(cfg_file):
                os.remove(cfg_file)
                print("Info: remove %s" % cfg_file)
            else:
                print("Info: %s not exist" % cfg_file)
            
            
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
        pxe.generate_dhcp_pxe()
        
def parser_arg(argv=None):
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_description = "This is used for generate pxe and ks file."
    program_name = os.path.basename(sys.argv[0])

    try:
        parser = ArgumentParser(description=program_description, 
                                formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-p", "--pxe", dest="dhcp", 
                            action="store_true", 
                            help="generate dhcp in dnsmasq folder [default: %(default)s]")
        parser.add_argument("-f", "--file", default="pxe.cfg", dest="file",
                            help="set config file [default: %(default)s]")
        parser.add_argument("-t", "--type", dest="type", help="set type")
        parser.add_argument("-i", "--ip", dest="ip", help="set ipaddress")
        parser.add_argument("-n", "--hostname", dest="hostname", help="set hostname")
        parser.add_argument("-m", "--mac", dest="mac", help="set mac address")
        parser.add_argument("-d", "--delete", dest="delete", 
                            action="store_true", 
                            help="delete mac file")
        # Process arguments
        args = parser.parse_args()
        
        if not args.mac or not args.type:
            parser.print_help()
            sys.exit()
            
        pxe = PXE(args.file, args.mac)
            
        if args.dhcp:
            pxe.generate_dhcp_pxe()
            
        if args.delete:
            pxe.delete_pxe(args.type)
            return 0
        
        if args.ip and args.hostname:
            if args.type=='xenserver' or args.type=='xcp':
                pxe.setup_xen_pxe(args.ip, args.hostname, args.type)
            elif args.type=='centos':
                pxe.setup_centos_pxe(args.ip, args.hostname)
            elif args.type=='esxi':
                pxe.setup_esxi_pxe(args.ip, args.hostname)
            return 0
       
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2
    
if __name__ == "__main__":
    parser_arg()
    