import os, shutil
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt
from tabulate import tabulate

from control import *

#
# Commands
#

# command to add a new transation
def add(confDir, accounts, log, args):
    if 1 in args:
        if 3 in args:
            # manual entry
            if '@' in args[1]:
                title, loc = args[1].split('@')
                acct = args[2].upper()
                src = '-'
                cost = float(args[3])
                
                # get optional arguments
                date = getOpArg(args, 'date', default=dt.today().strftime('%m-%d-%Y')).replace('/', '-')
                note = getOpArg(args, 'note')
            else:
                print('First argument must be formated \"[title]@[location]\"')
                return
        else:
            print('Requires arguments \"[title]@[location] [account] [amount]\"')
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
        logFile = confDir + 'log.csv'
        log.to_csv(logFile, index=False)
    else:
        print('Invalid account provided!')

# show last x transactions based on criteria
def showHistory(confDir, accounts, log, args):
    # limit of transactions
    count = 5
    if 1 in args:
        count = int(args[1])

    # optional arguments
    acct = getOpArg(args, 'acct').upper()
    end = getOpArg(args, 'end')
    start = getOpArg(args, 'start')
    title = getOpArg(args, 'title')
    loc = getOpArg(args, 'loc')
    note = getOpArg(args, 'note')
    transType = getOpArg(args, 'transType')
    count = int(getOpArg(args, 'count', default=count))

    # confirm a proved account is real
    if acct and acct not in accounts:
        print('Invalid account provided')
        return

    # get and print results
    results = getLast(log, count, acct, start=start, end=end, title=title, location=loc, note=note, transType=transType)
    print(results)
    print('Total:', valueToString(results['amount'].sum()))

# list all accounts
def listAccounts(confDir, accounts, log, args):
    print('Current accounts:')
    for acct in accounts:
        print(acct)

# add a new acount
def addAccount(confDir, accounts, log, args):
    # prompt if name is not provided
    if 1 in args:
        newAcct = args[1]
    else:
        newAcct = input('New account: ')

    # write to file
    accounts.append(newAcct)
    acctFile = confDir + 'accounts.csv'
    with open(acctFile, 'w+') as f:
        f.write(','.join([acct.upper().replace(' ', '') for acct in accounts]))

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# get basic info about an account
def accountInfo(confDir, accounts, log, args):
    # check account name
    if 1 not in args:
        print('An account name is required')
        return
    acct = args[1].upper()
    if acct not in accounts:
        print('Invalid account name,' + acct)
        return

    # get optional arguments
    starting = getOpArg(args, 'start')
    ending = getOpArg(args, 'end')
    reach = getOpArg(args, 'months', 6)

    # request data
    results = totalsPerUnitTime(log, 'months', acct=acct, start=starting, end=ending)

    # print title
    title = acct + ' Stats:'
    print(title)
    print('-'*len(title))

    # fetch last 6 months and print
    if reach != '0':
        rows = []
        for month, amount in results.iteritems():
            year, month = month
            month = months[month-1]
            rows.append([month + ' ' + str(year), valueToString(amount)])
        print(tabulate(rows[-int(reach):], headers=['Month', 'Delta']), '\n')

    add, sub, delta, toTrans, fromTrans, trans = getAccountInfo(log, acct, starting, ending)
    print(tabulate([['Count', toTrans, fromTrans], ['Value', valueToString(add), valueToString(sub)]], headers=['', 'In', 'Out']))
    print('\n\u001b[1mNet Total:', valueToString(delta))

# get balances of all accounts and total
def balance(confDir, accounts, log, args):
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
def export(confDir, accounts, log, args):
    if 1 in args:
        fileLoc = os.path.expanduser(args[1])
        if not fileLoc.endswith('.csv'):
            fileLoc += '.csv'

        # optional arguments
        acct = getOpArg(args, 'acct').upper()
        end = getOpArg(args, 'end').upper()
        start = getOpArg(args, 'start').upper()
        title = getOpArg(args, 'title')
        loc = getOpArg(args, 'loc')
        note = getOpArg(args, 'note')
        transType = getOpArg(args, 'transType').lower()
        
        # fetch items to export
        items = filter(log, acct=acct, start=start, end=end, title=title, location=loc, note=note, transType=transType)
        items.to_csv(fileLoc, index=False)
        print('Exported', len(items.index), 'items to', fileLoc)
    else:
        print('Requires at least 1 argument, the file location')

# link the directory else where (dropbox for example)
def link(confDir, accounts, log, args):
    if 1 in args:
        to = os.path.expanduser(args[1])
        shutil.move(confDir, to)
        print('Moved data to', to)
        if confDir.endswith('/'):
            confDir = confDir[:-1]
        os.symlink(to, confDir)
        print('Linked', confDir, 'to', to)
    else:
        print('Requires at least 1 argument, the directory to link to')

# plot an account's value over time
def plot(confDir, accounts, log, args):
    # get unit of time
    units = 'days'
    if 1 in args:
        units = args[1]

    # get optional arguments
    acct = getOpArg(args, 'acct').upper()
    start = getOpArg(args, 'start').upper()
    end = getOpArg(args, 'end').upper()
    invert = getOpArg(args, 'invert', default=False)
    points = getOpArg(args, 'dots', default=False)
    noLine = getOpArg(args, 'noline', default=False)
    allPoints = getOpArg(args, 'alldays', default=False)
    totals = getOpArg(args, 'totals', default=False)

    # request data
    results = totalsPerUnitTime(log, units, acct=acct, start=start, end=end)

    # give up if request failed
    if results.empty:
        print('No results found')
        return

    style = ''
    if points or noLine:
        style += '.'
    if not noLine:
        style += '-'

    # plot in a new window
    fig, ax = plt.subplots()
    sums = results
    kind = 'bar'
    if not totals:
        sums = sums.cumsum()
        kind = 'line'
    elif start == '':
        sums = sums[1:]
    
    if allPoints:
        sums.index = pd.to_datetime(sums.index, format='%Y/%m/%d')
        sums = sums.resample('D').fillna(method='ffill')
        
    sums.plot(kind=kind, ax=ax, style=style)
    low, hi = ax.get_ylim()
    if invert:
        plt.ylim(hi, low)
    plt.show()

# give help output
def helpCmd(confDir, accounts, log, args):
    print('Commands')
    print('--------')
    for key in cmds:
        _, msg = cmds[key]
        print(key, '-', msg)

# warn a command is unknown
def unknown(confDir, accounts, log, args):
    print('Invalid command,', args['cmd'])

# dictionary of commands  
cmds = dict({
    'add': (add, 'Add a new item to the log.'),
    'history': (showHistory, 'Display the last X items, default is 5.'),
    'hist': (showHistory, 'Shorter form of the history command.'),
    'listAccts': (listAccounts, 'List all known accounts.'),
    'newAcct': (addAccount, 'Add a new account.'),
    'acctInfo': (accountInfo, 'Display a brief summary of a given account.'),
    'balance': (balance, 'Provide the balance of all accounts, as well as the total.'),
    'bal': (balance, 'Shorter form of the balance command.'),
    'help': (helpCmd, 'List and describe all command options.'),
    'export': (export, 'Export entries to a new file.'),
    'plot': (plot, 'Plot total value per day/month over time.'),
    'link': (link, 'Link the configuration directory to a given directory.')
})