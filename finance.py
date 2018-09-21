import sys, os, shutil
import pandas as pd
from datetime import datetime as dt
from decimal import *

#
# Helper Functions
#

# Prompt for creating list of accounts
def setupAccts(acctFile):
    accounts = []
    newAcct = ''
    while newAcct != 'done':
        if newAcct is not '':
            accounts.append(newAcct)
        newAcct = input('Enter a new account (\'done\' to finish): ')
        if '2' in newAcct:
            newAcct = ''
            print('An account name cannot have \'2\' in it')
    with open(acctFile, 'w+') as f:
        f.write(','.join([acct.upper().replace(' ', '') for acct in accounts]))

# Initiates log file
def setupLog(logFile):
    with open(logFile, 'w+') as f:
        f.write('index,title,location,date,from,to,amount,note')

# TODO account for new unprocessed dates in date column
# A history/search tool
def getLast(log, count, acct='', start='', end='', title='', location='', note='', transType=''):
    hLog = filter(log, acct=acct, start=start, end=end, title=title, location=location, note=note, transType=transType)
    return hLog.tail(count).sort_values('date')

# Filter the database
def filter(log, acct='', start='', end='', title='', location='', note='', transType=''):
    hLog = log
    if acct != '':
        hLog = hLog[(hLog['from'] == acct) | (hLog['to'] == acct)]
    if start != '':
        hLog = hLog[hLog['date'] >= dt.strptime(start, '%m/%d/%Y')]
    if end != '':
        hLog = hLog[hLog['date'] < dt.strptime(end, '%m/%d/%Y')]
    if title != '':
        hLog = hLog[hLog['title'].str.contains(title)]
    if location != '':
        hLog = hLog[hLog['location'].str.contains(location)]
    if note != '':
        hLog = hLog[hLog['note'].str.contains(note)]
    if transType == 'to':
        hLog = hLog[(hLog['from'] == '-') & (hLog['to'] != '-')]
    elif transType == 'from':
        hLog = hLog[(hLog['from'] != '-') & (hLog['to'] == '-')]
    elif transType == 'transfer':
        hLog = hLog[(hLog['from'] != '-') & (hLog['to'] != '-')]
    return hLog

# Get a optional arguments value, provide default if not provided
def getOpArg(args, arg, default=''):
    val = default
    if arg in args:
        val = args[args.index(arg) + 1]
    return val

# Gets basic account stats
def getAccountInfo(log, account, start='', end=''):
    cLog = log

    # filter by date (optional)
    if start != '':
        cLog = cLog[cLog['date'] >= dt.strptime(start, '%m/%d/%Y')]
    if end != '':
        cLog = cLog[cLog['date'] < dt.strptime(end, '%m/%d/%Y')]

    # get all items
    tos = cLog[cLog['to'] == account]
    froms = cLog[cLog['from'] == account]

    # add values
    add = tos['amount'].sum()
    sub = froms['amount'].sum()
    delta = add - sub

    # count transactions
    toTrans = tos.shape[0]
    fromTrans = froms.shape[0]
    trans = toTrans + fromTrans
    return add, sub, delta, toTrans, fromTrans, trans

# converts a dollar value to a pretty string
def valueToString(value):
    valStr = str(round(value, 2))

    # add dollar sign
    if value < 0:
        valStr = '-$' + valStr[1:]
    else:
        valStr = '$' + valStr

    # add commas
    digits = len(str(abs(int(value))))
    decs = len(valStr[valStr.index('.')+1:])
    for i in range(max(2 - decs, 0)):
        valStr += '0'
    
    commas = int((digits-1) / 3 )
    for i in range(commas):
        pIndex = valStr.index('.')
        cIndex = pIndex - (i + 1) * 3 - i
        valStr = valStr[:cIndex] + ',' + valStr[cIndex:]
    return valStr

#
# Commands
#

# command to add a new transation
def add(args):
    if len(args) > 1:
        # manual entry
        title, loc = args[1].split('@')
        acct = args[2].upper()
        src = '-'
        cost = float(args[3])
        
        # get optional arguments
        date = getOpArg(args, '--date', default=dt.today().strftime('%m-%d-%Y')).replace('/', '-')
        note = getOpArg(args, '--note')
    else:
        # guided entry
        title = input('Title: ')
        loc = input('Location: ')
        cost = input('Value (negative if spent): ')
        acct = input('Account (\'2\' between accounts if transfer): ')
        print('The following requests are optional..')
        date = input('Date (mm/dd/yyyy):')
        note = input('Note: ')

    # process account
    if '2' in acct:
        src, acct = acct.split('2')
    elif cost < 0:
        src = acct
        acct = '-'
        cost = abs(cost)

    # add to log
    if (src in accounts or src == '-') and (acct in accounts or acct == '-'):
        log.loc[log.shape[0]] = [title, loc, date, src, acct, cost, note]
        #print(getLast(log, 5)) TODO
        log.to_csv(logFile)
    else:
        print('Invalid account provided!')

# show last x transactions based on criteria
def showHistory(args):
    # limit of transactions
    count = 5
    if len(args) > 1 and '-' not in args[1]:
        count = int(args[1])

    # optional arguments
    acct = getOpArg(args, '--acct').upper()
    end = getOpArg(args, '--end')
    start = getOpArg(args, '--start')
    title = getOpArg(args, '--title')
    loc = getOpArg(args, '--loc')
    note = getOpArg(args, '--note')
    transType = getOpArg(args, '--transType')
    count = int(getOpArg(args, '--count', default=count))

    if acct != '' and acct not in accounts:
        print('Invalid account provided')
        return
    results = getLast(log, count, acct, start=start, end=end, title=title, location=loc, note=note, transType=transType)
    print(results)
    print('Total:', valueToString(results['amount'].sum()))

# list all accounts
def listAccounts(args):
    print('Current accounts:')
    for acct in accounts:
        print(acct)

# add a new acount
def addAccount(args):
    # prompt if name is not provided
    if len(args) == 1:
        newAcct = input('New account: ')
    else:
        newAcct = args[1]

    # write to file
    accounts.append(newAcct)
    with open(acctFile, 'w+') as f:
        f.write(','.join([acct.upper().replace(' ', '') for acct in accounts]))

# get basic info about an account
def accountInfo(args):
    if len(args) == 1:
        print('An account name is required')
        return
    acct = args[1].upper()
    if acct not in accounts:
        print('Invalid account name,' + acct)
        return

    # get optional arguments
    starting = getOpArg(args, '--start')
    ending = getOpArg(args, '--end')

    # fetch and print stats
    title = acct + ' Stats:'
    print(title)
    print('-'*len(title))
    add, sub, delta, toTrans, fromTrans, trans = getAccountInfo(log, acct, starting, ending)
    print('Transactions: +', toTrans, ' -', fromTrans, ' =', trans, sep='')
    print('Delta: +', add, ' -', sub, sep='')
    print('\u001b[1mTotal:', valueToString(delta))

# get balances of all accounts and total
def balance(args):
    total = 0
    longestName = 0
    longestCost = 0
    accts = []
    # get each accounts balance and process
    for acct in accounts:
        _,_, delta, _,_,_ = getAccountInfo(log, acct)
        if len(acct) > longestName:
            longestName = len(acct)
        valStr =  valueToString(delta)
        dStr = valStr[:str(valStr).index('.')]
        if len(dStr) > longestCost:
            longestCost = len(dStr)
        accts.append(acct + '#' + valStr)
        total += delta

    # process total
    acct = 'Total'
    delta = total 
    if len(acct) > longestName:
        longestName = len(acct)
    valStr =  valueToString(delta)
    dStr = valStr[:str(valStr).index('.')]
    if len(dStr) > longestCost:
        longestCost = len(dStr)
    accts.append(acct + '#' + valStr)

    # display info
    print('Current Balances:')
    print('-----------------')
    for acct in accts:
        name, delta = acct.split('#')
        dStr = delta[:str(delta).index('.')]
        spaces = 1 + (longestName - len(name)) + (longestCost - len(dStr))
        if name == 'Total':
            name = '\u001b[1mTotal'
        print(name, ':', ' '*spaces, delta, sep='')

# exports data to a csv file
def export(args):
    if len(args) > 1:
        fileLoc = os.path.expanduser(args[1])
        if not fileLoc.endswith('.csv'):
            fileLoc += '.csv'

        # optional arguments
        acct = getOpArg(args, '--acct').upper()
        end = getOpArg(args, '--end').upper()
        start = getOpArg(args, '--start').upper()
        title = getOpArg(args, '--title')
        loc = getOpArg(args, '--loc')
        note = getOpArg(args, '--note')
        transType = getOpArg(args, '--transType').lower()
        
        items = filter(log, acct=acct, start=start, end=end, title=title, location=loc, note=note, transType=transType)
        items.to_csv(fileLoc)
        print('Exported', len(items.index), 'items to', fileLoc)
    else:
        print('Requires at least 1 argument, the file location')

# link the directory else where (dropbox for example)
def link(args):
    global confDir
    if len(args) > 1:
        to = os.path.expanduser(args[1])
        shutil.move(confDir, to)
        print('Moved data to', to)
        if confDir.endswith('/'):
            confDir = confDir[:-1]
        os.symlink(to, confDir)
        print('Linked', confDir, 'to', to)
    else:
        print('Requires at least 1 argument, the directory to link to')

# give help output
def helpCmd(args):
    print('Commands')
    print('--------')
    for key in cmds:
        _, msg = cmds[key]
        print(key, '-', msg)

# warn a command is unknown
def unknown(args):
    print('Invalid command,', args[0])

# dictionary of commands  
cmds = dict({
    'add': (add, 'Add a new item to the log.'),
    'hist': (showHistory, 'Display the last X items, default is 5.'),
    'listAccts': (listAccounts, 'List all known accounts.'),
    'newAcct': (addAccount, 'Add a new account.'),
    'acctInfo': (accountInfo, 'Display a brief summary of a given account'),
    'balance': (balance, 'Provide the balance of all accounts, as well as the total.'),
    'help': (helpCmd, 'List and describe all command options'),
    'export': (export, 'Export entries to a new file.'),
    'link': (link, 'Link the configuration directory to a given directory.')
})

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
    fn(args)
else:
    unknown(args)
