import sys, os
import pandas as pd

from control import *
from commands import *

#
# Main Execution
#

# process all arguments first
def processCmd(args):
    argDict = {}
    required = True
    if len(args) > 0 and args[-1][0:2] == '--':
        print('Invalid argument', args[-1], 'requires a value.')
        exit()
    for i, arg in enumerate(args):
        if arg[0] == '-' and not arg[1].isdigit():
            required = False
            if arg[1] == '-':
                nextArg = args[i+1]
                if nextArg[0] != '-':
                    argDict[arg[2:]] = nextArg
                else:
                    print('Invalid argument', arg, 'requires a value.')
                    exit()
            else:
                argDict[arg[1:]] = 'True'
        elif required:
            if i == 0:
                argDict['cmd'] = arg
            else:
                argDict[i] = arg
    
    return argDict

argDict = processCmd(sys.argv[1:])
#print('Arguments:', str(argDict))

finances = load(argDict)

# get command
mode = 'help'
if 'cmd' in argDict:
    mode = argDict['cmd']

# execute command
if mode in cmds:
    fn = cmds[mode][0]
    fn(finances, argDict)
else:
    unknown(finances, argDict)