import sys, os
import pandas as pd

from control import *
from commands import *

#
# Main Execution
#

args = sys.argv[1:]
argDict = {}

# process all arguments first
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

#print('Arguments:', str(argDict))

# use default or provided config file
confDir = '~/.config/finance'
if 'config' in argDict:
    confDir = argDict['config']
    args = args[:i]
confDir = os.path.expanduser(confDir)

if confDir[-1] != '/':
    confDir += '/'

acctFile = confDir + 'accounts.csv'
catFile = confDir + 'categories.csv'
logFile = confDir + 'log.csv'

# create config file if they don't exist
if not os.path.exists(confDir):
    choice = input('No configuration exists. Would you like to link to an existing configuration directory? [y/N] ')
    if choice.lower() == 'y':
        to = input('Where is the existing directory: ')
        to = os.path.expanduser(to)
        os.symlink(to, confDir[:-1])
    else:
        print('Creating new configuration...')
        os.makedirs(confDir)

if not os.path.exists(acctFile):
    setupAccts(acctFile)

if not os.path.exists(catFile):
    setupCats(catFile)

if not os.path.exists(logFile):
    setupLog(logFile)

# import data
with open(acctFile, 'r') as f:
    acctStr = f.read()
    accounts = acctStr.split(',')

categories = {}
with open(catFile, 'r') as f:
    catLines = f.read().split('\n')
    for line in catLines:
        parts = line.split(',')
        if len(parts) == 4:
            name = parts[0]
            titles = parts[1].split(':')
            if len(titles) == 1 and titles[0] == '':
                titles = []
            locs = parts[2].split(':')
            if len(locs) == 1 and locs[0] == '':
                locs = []
            accts = parts[3].split(':')
            if len(accts) == 1 and accts[0] == '':
                accts = []
            categories[name] = [titles, locs, accts]

log = pd.read_csv(logFile, sep=',', header=0, parse_dates=['date'])[['title', 'location', 'date', 'from', 'to', 'amount', 'note']]

# get command
mode = 'help'
if 'cmd' in argDict:
    mode = argDict['cmd']

# execute command
if mode in cmds:
    fn = cmds[mode][0]
    fn(confDir, accounts, categories, log, argDict)
else:
    unknown(confDir, accounts, categories, log, argDict)