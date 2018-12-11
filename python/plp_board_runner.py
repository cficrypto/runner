# -*- coding: utf-8 -*-
import argparse
from plp_platform import *

import os
import os.path
import time
import plptree

def execCmd(cmd):
    print ('Executing command: ' + cmd)
    return os.system(cmd)

class Runner(Platform):

    def __init__(self, config, js_config):

        super(Runner, self).__init__(config, js_config)
        
        parser = config.getParser()

        parser.add_argument("--binary", dest="binary",
                            help='specify the binary to be loaded')
                        
        parser.add_argument("--pulp-core-archi", dest="pulpCoreArchi",
                            help='specify the core architecture to be simulated', default="or1k")
        parser.add_argument("--pulp-archi", dest="pulpArchi",
                            help='specify the PULP architecture to be simulated', default="mia")
        parser.add_argument("--load", dest="load",
                            help='specify the way the binary is loaded', default=None)
        parser.add_argument("--avr-load", dest="avrLoader",
                            help='use AVR loader', action="store_true", default=False)
        parser.add_argument("--use-dpi", dest="dpi",
                            help='use AVR loader', action="store_true", default=False)
        
        parser.add_argument("--devices", dest="devices", default=[], action="append",
                            help='specify platform devices')
        
        [args, otherArgs] = parser.parse_known_args()
   
        self.addCommand('run', 'Run execution')
        self.addCommand('prepare', 'Prepare binary')
        self.addCommand('copy', 'Copy binary')


    def reset(self):
        return 0


    def copy(self):
        return 0

    def header(self):
        binary = self.config.getOption('binary').split(':')[0]
        if execCmd("objcopy --srec-len 1 --output-target=srec %s %s.s19" % (binary, os.path.basename(binary))) != 0: return -1
        if execCmd("s19toheader.py %s.s19 " % (os.path.basename(binary))) != 0: return -1
        return 0

    def prepare(self):
        return 0

    def run(self):

        binary = self.config.getOption('binary')
        if binary is None:
            raise Exception("No binary specified")

        if binary.find(':') != -1:
            binary, mask = self.config.getOption('binary').split(':')
        else:
            mask = "1"

        if self.config.getOption('load') == 'flasher':
            flashOpt = '-f %s' % (os.path.join(os.environ.get('PULP_SDK_HOME'), 'install/%s/bin/flash_programmer' % (self.config.getOption('pulpCoreArchi'))))
        else:
            flashOpt = ''


        if self.get_json().get_child_str('**/chip/name') not in ['honey', 'mia']:

            if self.get_json().get('**/gdb/active').get_bool():
                commands_name = '**/debug_bridge/gdb_commands'
            else:
                commands_name = '**/debug_bridge/commands'

            commands = " ".join(self.get_json().get_child_str(commands_name).split(','))


            if self.get_json().get_child_str('**/chip/name') in ['gap']:
                return execCmd('plpbridge --cable=ftdi@digilent --boot-mode=jtag --binary=%s --chip=gap %s' % (binary, commands))
            elif self.get_json().get_child_str('**/chip/name') in ['wolfe']:
                return execCmd('plpbridge --cable=ftdi --boot-mode=jtag --binary=%s --chip=wolfe %s' % (binary, commands))
            elif self.get_json().get_child_str('**/chip/name') in ['vivosoc3']:
                return execCmd('plpbridge --cable=ftdi --binary=%s --chip=vivosoc3 %s' % (binary, commands))
            else:
                return execCmd('plpbridge --binary=%s --config=%s %s' % (binary, self.config.getOption('configFile'), commands))

        elif self.config.getOption('pulpArchi') == 'pulp3':
            return execCmd("debug_bridge -c ft2232 -b %s --binary %s --load --late-reset --loop --printf --start %s %s" % (self.config.getOption('pulpArchi').replace('-riscv', ''), binary, mask, flashOpt))
        else:
            if self.config.getOption('avrLoader'):
              return execCmd("debug_bridge -c vivo -b vivosoc2 --binary %s --load --loop --printf --start %s %s" % (binary, mask, flashOpt))
            else:
              return execCmd("debug_bridge -c ft2232 -b %s --reset --binary %s --load --loop --printf --start %s %s" % (self.config.getOption('pulpArchi').replace('-riscv', ''), binary, mask, flashOpt))
          
#        else:
#          if self.reset() != 0: return -1
#          if binary != None:
#            if self.copy() != 0:
#              return -1
#
#            return execCmd("vivo-boot --start --poll")
