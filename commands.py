import os, shutil
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt
from tabulate import tabulate

from control import *

#
# Commands
#

# command to delete a row
def delete(confDir, accounts, log, args):
    if 1 in args:
        i = int(args[1])
        answer = input(' '.join(['Would you like to remove?', log.loc[i, 'title'], log.loc[i, 'location'], log.loc[i, 'to'], log.loc[i, 'from'], str(log.loc[i, 'amount']), '[y/N] ']))
        if answer == 'y':
            log = log.drop(i)
            logFile = confDir + 'log.csv'
            save(log, logFile)
            print('Item deleted')
    else:
        print('Please provide a row number')

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
        save(log, logFile)
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
    return results

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
            rows.append([month, valueToString(amount)])
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
        save(items, fileLoc)
        print('Exported', len(items.index), 'items to', fileLoc)
    else:
        print('Requires at least 1 argument, the file location')

# plot historical values
def visualHistory(confDir, accounts, log, args):
    results = showHistory(confDir, accounts, log, args)
    fig, ax = plt.subplots()
    ax = results.plot(x='date', y='amount', kind='bar', ax=ax, title='History')
    ax.set_xlabel('Transaction')
    ax.set_ylabel('Absolute Dollars')
    plt.show()

# show unique values in a given column
def unique(confDir, accounts, log, args):
    if 1 in args:
        column = args[1]
        if column in log:
            unique = log[column].unique()
            unique.sort()
            print(unique)
        else:
            print('Column not found please choose from:', ', '.join(log.columns))
    else:
        print('Requires 1 argument, the column name')

# replace all matching values in column
def replaceAll(confDir, accounts, log, args):
    if 3 in args:
        column = args[1]
        old = '^' + args[2] + '$'
        new = args[3]
        if column in log:
            log[column] = log[column].replace({old: new}, regex=True)
            logFile = confDir + 'log.csv'
            save(log, logFile)
        else:
            print('Column not found please choose from:', ', '.join(log.columns))
    else:
        print('Requires 3 arguments, the column name, find string, and replace string')

# plot an account's value over time
def plot(confDir, accounts, log, args):
    # get unit of time, default is days
    units = 'days'
    if 1 in args:
        units = args[1]
    units = units.lower()

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

    # set style of line
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
    
    # fill empty points
    if allPoints and units.startswith('day'):
        sums.index = pd.to_datetime(sums.index, format='%Y/%m/%d')
        sums = sums.resample('D').fillna(method='ffill')
    elif allPoints:
        print('-alldays can only be used with the units as days')

    # build title of plot
    if acct:
        title = acct[0] + acct[1:].lower() + ' Account'
    else:
        title = 'Total'
    if totals:
        title += ' Delta'
    title += ' by '
    if units.startswith('day'):
        units = 'Day'
    elif units.startswith('week'):
        units = 'Week'
    elif units.startswith('month'):
        units = 'Month'
    elif units.startswith('quarter'):
        units = 'Quarter'
    elif units.startswith('year'):
        units = 'Year'
    title += units
    
    # display plot
    ax = sums.plot(kind=kind, ax=ax, style=style, title=title)
    ax.set_xlabel(units)
    ax.set_ylabel('Dollars')
    if invert:
        low, hi = ax.get_ylim()
        plt.ylim(hi, low)
    plt.show()

# reset the configuration
def reset(confDir, accounts, log, args):
    confirm = input('Are you sure you want to delete everything? [y/N] ')
    if confirm.lower() == 'y':
        confDir = confDir[:-1]
        if os.path.islink(confDir):
            os.unlink(confDir)
        else:
            shutil.rmtree(confDir)
        print('Reset complete')

# give help output
def helpCmd(confDir, accounts, log, args):
    if 1 in args:
        # print description of given command
        cmd = args[1]
        if cmd in cmds:
            print(cmd)
            print('-' * len(cmd))
            print(cmds[cmd][1])
            print(cmds[cmd][2])
        else:
            print('Command \"', cmd, '\" not found.', sep='')
    else:
        # if no command is given, summarize all commands
        print('Commands')
        print('--------')
        for key in cmds:
            print(key, '-', cmds[key][1])

# warn a command is unknown
def unknown(confDir, accounts, log, args):
    print('Invalid command,', args['cmd'])

# dictionary of commands  
cmds = dict({
    'acctInfo': (accountInfo, 'Display a brief summary of a given account.', 'acctInfo account [--start start_date] [--end end_date] [--months months_back]'),
    'add': (add, 'Add a new item to the log.', 'add title@location account amount [--date date] [--note note]'),
    'balance': (balance, 'Provide the balance of all accounts, as well as the total.', 'balance'),
    'bal': (balance, 'Shorter form of the balance command.', 'bal'),
    'delete': (delete, 'Remove an entry from the log.', 'delete entry_index'),
    'del': (delete, 'Shorter form of the delete command.', 'del entry_index'),
    'export': (export, 'Export entries to a new file.', 'export log_file'),
    'help': (helpCmd, 'List and describe all command options.', 'help [command]'),
    'history': (showHistory, 'Display the last X items, default is 5.', 'history [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'hist': (showHistory, 'Shorter form of the history command.', 'hist [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'listAccts': (listAccounts, 'List all known accounts.', 'listAccts'),
    'newAcct': (addAccount, 'Add a new account.', 'newAcct account'),
    'plot': (plot, 'Plot total value per day/month over time.', 'plot [units] [--start start_date] [--end end_date] [--acct account] [-invert] [-dots] [-noline] [-alldays] [-totals]'),
    'replace': (replaceAll, 'Replace all matching strings in a given column.', 'replace [column] [find] [replace_with]'),
    'reset': (reset, 'Resets the existing configuration.', 'reset'),
    'unique': (unique, 'Gets all unique values in a given column.', 'unique [column]'),
    'visualHistory': (visualHistory, 'Display the last X items as a plot, default is 5.', 'visualHistory [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'vhist': (visualHistory, 'Shorter form of the visualHistory command.', 'vhist [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]')
})