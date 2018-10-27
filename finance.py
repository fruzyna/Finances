import sys, os
import pandas as pd

from control import *
from commands import *

#
# Main Execution
#

args = sys.argv[1:]
#print('Arguments:', str(args))

# use default or provided config file
confDir = '~/.config/finance'
if '--config' in args:
    i = args.index('--config')
    confDir = args[i+1]
    args = args[:i]
confDir = os.path.expanduser(confDir)

if confDir[-1] != '/':
    confDir += '/'

acctFile = confDir + 'accounts.csv'
logFile = confDir + 'log.csv'

# create config file if they don't exist
if not os.path.exists(confDir):
    os.makedirs(confDir)

if not os.path.exists(acctFile):
    setupAccts(acctFile)

if not os.path.exists(logFile):
    setupLog(logFile)

# import data
with open(acctFile, 'r') as f:
    acctStr = f.read()
    accounts = acctStr.split(',')
log = pd.read_csv(logFile, sep=',', header=0, index_col=0, parse_dates=['date'])

# get command
mode = 'help'
if len(args) > 0:
    mode = args[0]
print()

# execute command
if mode in cmds:
    fn,_ = cmds[mode]
    fn(accounts, log, args)
else:
    unknown(accounts, log, args)