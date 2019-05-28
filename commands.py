import os, shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
from datetime import timedelta
from tabulate import tabulate

from control import *

#
# Commands
#

# command to delete a row
def delete(confDir, accounts, categories, log, args):
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
def add(confDir, accounts, categories, log, args):
    if 3 in args:
        # manual entry
        if '@' in args[1]:
            title, loc = args[1].split('@')
            acct = args[2]
            src = '-'
            cost = args[3]
            
            # get optional arguments
            date = getOpArg(args, 'date', default=dt.today().strftime(dateFormat))
            note = getOpArg(args, 'note')
        else:
            print('First argument must be formated "[title]@[location]"')
            return
    else:
        print('Requires arguments "[title]@[location] [account] [amount]"')

    # process account
    if '2' in acct:
        src, acct = acct.split('2')
    elif cost[0] == '-':
        src = acct
        acct = '-'
        cost = cost[1:]

    # add to log
    log.loc[log.shape[0]] = [correctFormat('title', title), correctFormat('location', loc), correctFormat('date', date), correctFormat('from', src, accounts=accounts), correctFormat('to', acct, accounts=accounts), correctFormat('amount', cost), correctFormat('note', note)]
    logFile = confDir + 'log.csv'
    save(log, logFile)

# show last x transactions based on criteria
def showHistory(confDir, accounts, categories, log, args):
    # limit of transactions
    count = 5
    if 1 in args:
        count = int(args[1])

    # optional arguments
    acct        = correctFormat('account', getOpArg(args, 'acct'), accounts=accounts)
    end         = correctFormat('date', getOpArg(args, 'end'))
    start       = correctFormat('date', getOpArg(args, 'start'))
    title       = correctFormat('title', getOpArg(args, 'title'))
    loc         = correctFormat('location', getOpArg(args, 'loc'))
    note        = correctFormat('note', getOpArg(args, 'note'))
    category    = correctFormat('category', getOpArg(args, 'cat'), categories=categories)
    transType   = getOpArg(args, 'transType')
    count       = int(getOpArg(args, 'count', default=count))

    # get and print results
    results = getLast(log, count, categories, acct=acct, start=start, end=end, title=title, location=loc, note=note, transType=transType, category=category)
    print(results)
    print('Total:', valueToString(results['amount'].sum()))
    return results

# display the progress of a category goal in the current month
def goalProgress(confDir, accounts, categories, log, args):
    if 1 in args:
        # get category and mont
        catName = correctFormat('category', args[1], categories=categories)
        today = dt.today()
        if 2 in args:
            today = today.replace(month=int(args[2]))
        if 3 in args:
            today = today.replace(year=int(args[3]))

        # fetch progress for month
        month, first, last, spent, goal, progress = getMonthProgress(log, catName, categories, today.month, today.year)

        # print results
        print(catName, 'from', first, 'to', last)
        print(month)
        if goal > 0:
            print(tabulate([['Spent', valueToString(spent)], ['Goal', valueToString(goal)], ['Progress', str(progress) + '%']]))
        else:
            print('Spent:', valueToString(spent))
    else:
        print('Requires at least 1 argument, the name of the category.')

# display the progress of a category goal in the current month
def monthlyGoal(confDir, accounts, categories, log, args):
    if 1 in args:
        # get parameters
        catName = correctFormat('category', args[1], categories=categories)
        plot = getOpArg(args, 'plot', default=False)
        months = 6
        if 2 in args:
            months = int(args[2])

        today = dt.today()
        m = today.month
        y = today.year
        dates = []
        spents = []
        goals = []
        progresses = []
        percents = []

        # get each months progress
        for i in range(months):
            _, first, _, spent, goal, progress = getMonthProgress(log, catName, categories, m, y)

            # advance to previous month
            if m == 1:
                m = 12
                y -= 1
            else:
                m -= 1

            # add values to lists
            dates.append(first)
            spents.append(valueToString(spent))
            if goal > 0:
                goals.append(valueToString(goal))
                progresses.append(str(progress) + '%')
                percents.append(progress)

        # reverse lists
        dates.reverse()
        spents.reverse()
        goals.reverse()
        progresses.reverse()
        percents.reverse()

        # add labels and make table
        dates = ['Date'] + dates
        spents = ['Spent'] + spents
        goals = ['Goal'] + goals
        progresses = ['Progress'] + progresses
        print(tabulate([dates, spents, goals, progresses]))

        if plot:
            # determine what is above and below goal
            above = np.maximum(np.array(percents) - 100, 0)
            below = np.minimum(np.array(percents), 100)

            # plot percentages
            fig, ax = plt.subplots() 
            ax.bar(dates[1:], below, 0.35, color='g')
            ax.bar(dates[1:], above, 0.35, color='r', bottom=100)
            ax.plot(dates[1:], [100] * months, 'k--')
            ax.set_title(catName + ' Goal Progress over Last ' + str(months) + ' Months')
            ax.set_xlabel('Month')
            ax.set_ylabel('Percent of Goal')
            plt.show()
    else:
        print('Requires at least 1 argument, the name of the category.')

# list all accounts
def listAccounts(confDir, accounts, categories, log, args):
    print('Current accounts:')
    print('\n'.join(accounts))

# list all accounts
def listCategories(confDir, accounts, categories, log, args):
    print('Current categories:')
    print('\n'.join(categories))

# add a new acount
def addAccount(confDir, accounts, categories, log, args):
    # prompt if name is not provided
    if 1 in args:
        newAcct = args[1]
    else:
        newAcct = input('New account: ')
    newAcct = correctFormat('account', newAcct, new=True)

    # write to file
    accounts.append(newAcct)
    acctFile = confDir + 'accounts.csv'
    with open(acctFile, 'w+') as f:
        f.write(','.join(accounts))

# add a new category
def addCategory(confDir, accounts, categories, log, args):
    # prompt if name is not provided
    if 1 in args:
        name    = args[1]
        goal    = getOpArg(args, 'goal')
        titles  = getOpArg(args, 'title')
        locs    = getOpArg(args, 'loc')
        accts   = getOpArg(args, 'acct')
    else:
        name    = input('New category: ')
        goal    = input('Monthly Goal: ')
        print('Separate lists of options by commas')
        titles  = input('Accepted Titles: ')
        locs    = input('Accepted Locations: ')
        accts   = input('Accepted Accounts: ')

    name    = correctFormat('category', name, new=True)
    goal    = correctFormat('amount', goal)
    titles  = [correctFormat('title', title) for title in titles.split(',')]
    locs    = [correctFormat('location', loc) for loc in locs.split(',')]
    accts   = [correctFormat('account', acct, accounts=accounts) for acct in accts.split(',')]

    # write to file
    categories[name] = [goal, titles, locs, accts]
    catFile = confDir + 'categories.csv'
    with open(catFile, 'w+') as f:
        for catName in categories:
            cat = categories[catName]
            goal    = cat[0]
            titles  = cat[1]
            locs    = cat[2]
            accts   = cat[3]
            f.write(catName + ',' + goal + ',' + ':'.join(titles) + ',' + ':'.join(locs) + ',' + ':'.join(accts) + '\n')

# get basic info about an account
def accountInfo(confDir, accounts, categories, log, args):
    # check account name
    if 1 not in args:
        print('An account name is required')
        return
    acct = correctFormat('account', args[1], accounts=accounts)

    # get optional arguments
    starting = correctFormat('date', getOpArg(args, 'start'))
    ending   = correctFormat('date', getOpArg(args, 'end'))
    reach    = getOpArg(args, 'months', 6)

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
def balance(confDir, accounts, categories, log, args):
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
def export(confDir, accounts, categories, log, args):
    if 1 in args:
        fileLoc = os.path.expanduser(args[1])
        if not fileLoc.endswith('.csv'):
            fileLoc += '.csv'

        # optional arguments
        acct        = correctFormat('account', getOpArg(args, 'acct'))
        end         = correctFormat('date', getOpArg(args, 'end'))
        start       = correctFormat('date', getOpArg(args, 'start'))
        title       = correctFormat('title', getOpArg(args, 'title'))
        loc         = correctFormat('location', getOpArg(args, 'loc'))
        note        = correctFormat('note', getOpArg(args, 'note'))
        transType   = getOpArg(args, 'transType').lower()
        
        # fetch items to export
        items = filter(log, categories, acct=acct, start=start, end=end, title=title, location=loc, note=note, transType=transType)
        save(items, fileLoc)
        print('Exported', len(items.index), 'items to', fileLoc)
    else:
        print('Requires at least 1 argument, the file location')

# plot historical values
def visualHistory(confDir, accounts, categories, log, args):
    results = showHistory(confDir, accounts, categories, log, args)
    fig, ax = plt.subplots()
    ax = results.plot(x='date', y='amount', kind='bar', ax=ax, title='History')
    ax.set_xlabel('Transaction')
    ax.set_ylabel('Absolute Dollars')
    plt.show()

# show unique values in a given column
def unique(confDir, accounts, categories, log, args):
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
def replaceAll(confDir, accounts, categories, log, args):
    if 3 in args:
        column = args[1]
        if column in log:
            old = '^' + correctFormat(column, args[2], accounts=accounts) + '$'
            new = correctFormat(column, args[3], accounts=accounts)
            log[column] = log[column].replace({old: new}, regex=True)
            logFile = confDir + 'log.csv'
            save(log, logFile)
        else:
            print('Column not found please choose from:', ', '.join(log.columns))
    else:
        print('Requires 3 arguments, the column name, find string, and replace string')

# command to edit a value in a column
def edit(confDir, accounts, categories, log, args):
    if 2 in args:
        i = int(args[1])
        column = args[2]
        if column in log:
            if 3 in args:
                new = args[3]
            else:
                new = input('New value for ' + str(i) + ', ' + column + ' (' + log.loc[i, column] + '): ')
            log.loc[i, column] = correctFormat(column, new, accounts=accounts)
            logFile = confDir + 'log.csv'
            save(log, logFile)
        else:
            print('Column not found please choose from:', ', '.join(log.columns))
    else:
        print('Please provide a row number and column name')

# plot an account's value over time
def plot(confDir, accounts, categories, log, args):
    # get unit of time, default is days
    units = 'days'
    if 1 in args:
        units = args[1]
    units = units.lower()

    # get optional arguments
    acct        = correctFormat('account', getOpArg(args, 'acct'), accounts=accounts)
    cat         = correctFormat('category', getOpArg(args, 'cat'), categories=categories)
    start       = correctFormat('date', getOpArg(args, 'start'))
    end         = correctFormat('date', getOpArg(args, 'end'))
    invert      = getOpArg(args, 'invert', default=False)
    points      = getOpArg(args, 'dots', default=False)
    noLine      = getOpArg(args, 'noline', default=False)
    allPoints   = getOpArg(args, 'alldays', default=False)
    totals      = getOpArg(args, 'totals', default=False)

    # request data
    results = totalsPerUnitTime(log, units, categories, acct=acct, start=start, end=end, category=cat)

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
        sums.index = pd.to_datetime(sums.index, format=dateFormat)
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
def reset(confDir, accounts, categories, log, args):
    confirm = input('Are you sure you want to delete everything? [y/N] ')
    if confirm.lower() == 'y':
        confDir = confDir[:-1]
        if os.path.islink(confDir):
            os.unlink(confDir)
        else:
            shutil.rmtree(confDir)
        print('Reset complete')

# give help output
def helpCmd(confDir, accounts, categories, log, args):
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
def unknown(confDir, accounts, categories, log, args):
    print('Invalid command,', args['cmd'])

# dictionary of commands  
cmds = dict({
    'acctInfo': (accountInfo, 'Display a brief summary of a given account.', 'acctInfo account [--start start_date] [--end end_date] [--months months_back]'),
    'add': (add, 'Add a new item to the log.', 'add title@location account amount [--date date] [--note note]'),
    'balance': (balance, 'Provide the balance of all accounts, as well as the total.', 'balance'),
    'bal': (balance, 'Shorter form of the balance command.', 'bal'),
    'delete': (delete, 'Remove an entry from the log.', 'delete entry_index'),
    'del': (delete, 'Shorter form of the delete command.', 'del entry_index'),
    'edit': (edit, 'Edit a given value in an entry.', 'edit entry_index column'),
    'export': (export, 'Export entries to a new file.', 'export log_file'),
    'help': (helpCmd, 'List and describe all command options.', 'help [command]'),
    'history': (showHistory, 'Display the last X items, default is 5.', 'history [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'hist': (showHistory, 'Shorter form of the history command.', 'hist [count] [--start start_date] [--end end_date] [--acct account] [--cat category] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'listAccts': (listAccounts, 'List all known accounts.', 'listAccts'),
    'listCats': (listCategories, 'List all known categories.', 'listCats'),
    'newAcct': (addAccount, 'Add a new account.', 'newAcct account_name'),
    'newCat': (addCategory, 'Add a new category.', 'newCat category_name'),
    'plot': (plot, 'Plot total value per day/month over time.', 'plot [units] [--start start_date] [--end end_date] [--acct account] [-invert] [-dots] [-noline] [-alldays] [-totals]'),
    'progress': (goalProgress, 'Display current monthly progress of a category goal.', 'progress category_name [month_num] [year_num]'),
    'progressMonths': (monthlyGoal, 'Display goal results over the last few months.', 'progressMonths category_name number of months'),
    'replace': (replaceAll, 'Replace all matching strings in a given column.', 'replace column find replace_with'),
    'reset': (reset, 'Resets the existing configuration.', 'reset'),
    'unique': (unique, 'Gets all unique values in a given column.', 'unique column'),
    'visualHistory': (visualHistory, 'Display the last X items as a plot, default is 5.', 'visualHistory [count] [--start start_date] [--end end_date] [--cat category] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'vhist': (visualHistory, 'Shorter form of the visualHistory command.', 'vhist [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]')
})