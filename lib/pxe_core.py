#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# @author: david_dong

import os
import sys
import json
import platform
import ConfigParser
import subprocess
from jinja2 import Template
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter


def get_parent_path():
    current_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.abspath(os.path.join(current_path, os.pardir))


def mkdir_if_not_exist(folder):
    real_path = os.path.join(get_parent_path(), folder)
    if not os.path.exists(real_path):
        os.makedirs(real_path)
    return real_path


def get_config_from_cfg(config_file, section):
    filename = os.path.join(mkdir_if_not_exist('conf'), config_file)
    cf = ConfigParser.ConfigParser()
    cf.read(filename)
    return dict(cf.items(section))


def get_json_from_cfg(json_file):
    json_file = os.path.join(mkdir_if_not_exist('conf'), json_file)
    with open(json_file) as json_f:
        json_data = json.load(json_f)
    return json_data


def get_ip_suffix(ip_string):
    return ip_string.split('.')[-1]


def write_json_to_cfg(json_string, json_file):
    json_file = os.path.join(mkdir_if_not_exist('conf'), json_file)
    with open(json_file, 'w+') as json_f:
        json.dump(json_string, json_f, indent=4, sort_keys=True)


def generate_file_from_temp(**kwargs):
    src_file = os.path.join(
        mkdir_if_not_exist(kwargs['src_dir']), kwargs['src_file'])
    dest_file = os.path.join(
        mkdir_if_not_exist(kwargs['dest_dir']), kwargs['dest_file'])
    with open(src_file, "r") as f:
        template = Template(f.read())
    with open(dest_file, "w") as f:
        f.write(template.render(**kwargs))


def get_os_platform():
    system = platform.system()

    if system == "Linux":
        return "linux"
    elif system == "Windows":
        return "windows"
    else:
        return "others"


class CommandException(Exception):
    '''
    Base Exception for cmd_utils exceptions.
    Attributes:
        exc         - string message
        return_code - return code of command
    '''

    def __init__(self, exc, return_code=None):
        Exception.__init__(self)
        self.exc = exc
        self.return_code = return_code

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.exc


class ReturnCodeError(CommandException):
    """Raised when a command returns a non-zero exit code."""
    pass


class PXE():
    def __init__(self, ip, mac=None, conf_file='pxe.cfg', mac_file='mac.json'):
        self.gl_config = get_config_from_cfg(conf_file, 'global')
        self.conf_file = conf_file
        self.mac_addrs = get_json_from_cfg(mac_file)
        self.ip = ip
        if mac is not None:
            self.mac = mac
            self.mac_addrs.update(dict(ip, mac))
            write_json_to_cfg(self.mac_addrs, mac_file)
        elif ip in self.mac_addrs:
            self.mac = self.mac_addrs[ip]
        else:
            sys.exit()

        self.mac_name = '01-{0}'.format('-'.join(self.mac.lower().split(":")))
        self.filename = conf_file
        self.tftpboot = os.path.join(get_parent_path(),
                                     self.gl_config['tftp_root'])
        self.pxelinux = os.path.join(get_parent_path(),
                                     self.gl_config['tftp_root'],
                                     'pxelinux.cfg')
        self.answer_path = os.path.join(get_parent_path(),
                                        self.gl_config['www_root'],
                                        self.gl_config['kick_url'])
        self.temp = self.gl_config['temp_folder']

    def setup_xen_pxe(self, hostname, m_type='xenserver', suffix='62'):
        answer = self.mac_name + '.xml'
        config = get_config_from_cfg(self.conf_file, m_type + suffix)
        config.update({'answerfile': answer, 'xen_ipaddr': self.ip,
                       'xen_hostname': hostname,
                       'src_dir': self.temp, 'src_file': config['pxe_file'],
                       'dest_dir': self.pxelinux, 'dest_file': self.mac_name})
        config.update(**self.gl_config)
        generate_file_from_temp(**config)
        print("Info: generate %s in %s" % (self.mac_name, self.pxelinux))

        config.update({'src_dir': self.temp, 'src_file': config['kick_file'],
                       'dest_dir': self.answer_path, 'dest_file': answer})

        generate_file_from_temp(**config)
        print("Info: generate %s in %s" % (answer, self.answer_path))

    def setup_centos_pxe(self, hostname, m_type='centos', suffix='65'):
        answer = self.mac_name+'.ks'
        config = get_config_from_cfg(self.filename, m_type + suffix)
        config.update({'answerfile': answer, 'host_ipaddr': self.ip,
                       'hostname': hostname,
                       'src_dir': self.temp, 'src_file': config['pxe_file'],
                       'dest_dir': self.pxelinux, 'dest_file': self.mac_name})
        config.update(**self.gl_config)

        generate_file_from_temp(**config)
        print("Info: generate %s in %s" % (self.mac_name, self.pxelinux))

        config.update({'src_dir': self.temp, 'src_file': config['kick_file'],
                       'dest_dir': self.answer_path, 'dest_file': answer})
        generate_file_from_temp(**config)
        print("Info: generate %s in %s" % (answer, self.answer_path))

    def setup_esxi_pxe(self, hostname, m_type='esxi', suffix='55'):
        answer = '%s.ks' % self.mac_name
        cfgfile = '%s.cfg' % self.mac_name
        config = get_config_from_cfg(self.filename, m_type + suffix)
        config.update(**self.gl_config)
        config.update({'ksfile': answer, 'cfgfile': cfgfile,
                       'macaddr': self.mac, 'host_ipaddr': self.ip,
                       'hostname': hostname,
                       'src_dir': self.temp, 'src_file': config['pxe_file'],
                       'dest_dir': self.pxelinux, 'dest_file': self.mac_name})
        generate_file_from_temp(**config)
        print("Info: generate %s in %s" % (self.mac_name, self.pxelinux))

        config.update({'src_dir': self.temp, 'src_file': config['cfg_file'],
                       'dest_dir': self.answer_path, 'dest_file': cfgfile})
        generate_file_from_temp(**config)
        print("Info: generate ks: %s in %s" % (cfgfile, self.answer_path))

        config.update({'src_dir': self.temp, 'src_file': config['kick_file'],
                       'dest_dir': self.answer_path, 'dest_file': answer})
        generate_file_from_temp(**config)
        print("Info: generate ks: %s in %s" % (answer, self.answer_path))

    def delete_pxe(self, m_type):
        if m_type == 'xenserver' or m_type == 'xcp':
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
        if m_type == 'esxi':
            cfg_file = '%s.cfg' % self.mac_name
            cfg_file = os.path.join(self.answer_path, cfg_file)
            if os.path.isfile(cfg_file):
                os.remove(cfg_file)
                print("Info: remove %s" % cfg_file)
            else:
                print("Info: %s not exist" % cfg_file)

    def generate_dhcp_http_pxe(self, dhcp_name='dhcp',
                               http_name='lighttpd.conf'):
        dhcp_config = get_config_from_cfg(self.filename, 'dhcp')
        dhcp_config.update(**self.gl_config)
        dhcp_hosts = [dict(pxe_method=dhcp_config['pxe_method'],
                           mac=v, ip=k)
                      for (k, v) in self.mac_addrs.items() if v != '']

        dhcp_config.update({'dhcp_hosts': dhcp_hosts,
                            'tftp_root': self.tftpboot,
                            'src_dir': self.temp, 'src_file': 'dhcp.in',
                            'dest_dir': dhcp_config['dnsmasq_path'],
                            'dest_file': dhcp_name})
        system = get_os_platform()
        if system == "windows":
            dhcp_config['dnsmasq_path'] = 'final'
            dhcp_config['lighttpd_path'] = 'final'
        generate_file_from_temp(**dhcp_config)
        print("Info: generate dhcp: %s in %s" % (dhcp_name,
                                                 dhcp_config['dnsmasq_path']))

        dhcp_config.update({'wwwroot': os.path.join(
            get_parent_path(), self.gl_config['www_root'])})
        dhcp_config.update({'src_dir': self.temp, 'src_file': 'lighttpd.in',
                            'dest_dir': dhcp_config['lighttpd_path'],
                            'dest_file': http_name})
        generate_file_from_temp(**dhcp_config)
        print("Info: generate lighttpd: %s in %s" % (
            http_name, dhcp_config['lighttpd_path']))
        if system == "windows":
            sys.exit()
        self.execute_cmd('/etc/init.d/dnsmasq restart', '/root')
        self.execute_cmd('/etc/init.d/lighttpd restart', '/root')

    def execute_cmd(self, command, work_dir=None):
        if work_dir is not None:
            os.chdir(work_dir)  # Change to working directory

        # Run Command
        ps = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output = ps.communicate()[0]
        print output.strip('\n')
        return_code = ps.returncode
        # Throw exception if return code is not 0
        if return_code:
            exc = "%s\nCOMMAND:%s\nRET_CODE:%i" % (output, command,
                                                   return_code)
            raise ReturnCodeError(exc, return_code)


def run(ip_suffix, m_type):
    ip = '172.16.1.{}'.format(ip_suffix)
    pxe = PXE(ip)
    if m_type == 'xenserver' or m_type == 'xcp':
        pxe.setup_xen_pxe(m_type + ip_suffix, m_type)
    elif m_type == 'centos':
        pxe.setup_centos_pxe(m_type + ip_suffix)
    elif m_type == 'esxi':
        pxe.setup_esxi_pxe(m_type + ip_suffix)
    pxe.generate_dhcp_http_pxe()


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
        parser.add_argument(
            "-p", "--pxe", dest="dhcp",
            action="store_true",
            help="generate dhcp in dnsmasq folder [default: %(default)s]")
        parser.add_argument("-f", "--file", default="pxe.cfg", dest="file",
                            help="set config file [default: %(default)s]")
        parser.add_argument("-t", "--type", dest="type", help="set type")
        parser.add_argument("-i", "--ip", dest="ip", help="set ipaddress")
        parser.add_argument("-n", "--hostname", dest="hostname",
                            help="set hostname")
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
            pxe.generate_dhcp_http_pxe()

        if args.delete:
            pxe.delete_pxe(args.type)
            return 0

        if args.ip and args.hostname:
            if args.type == 'xenserver' or args.type == 'xcp':
                pxe.setup_xen_pxe(args.ip, args.hostname, args.type)
            elif args.type == 'centos':
                pxe.setup_centos_pxe(args.ip, args.hostname)
            elif args.type == 'esxi':
                pxe.setup_esxi_pxe(args.ip, args.hostname)
            return 0

        return 0
    except KeyboardInterrupt:
        # handle keyboard interrupt #
        return 0
    except Exception, e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help\n")
        return 2

if __name__ == '__main__':
    parser_arg()
