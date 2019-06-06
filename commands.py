import os, shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime as dt
from datetime import timedelta
from tabulate import tabulate

from control import *
from features import *

#
# Commands
#

# command to delete a row
def CLIdelete(finances, args):
    if 1 in args:
        i = int(args[1])
        log = finances.log
        answer = input(' '.join(['Would you like to remove?', log.loc[i, 'title'], log.loc[i, 'location'], log.loc[i, 'to'], log.loc[i, 'from'], str(log.loc[i, 'amount']), '[y/N] ']))
        if delete(finances, args[1], answer):
            print('Item deleted')
    else:
        print('Please provide a row number')

# command to add a new transation
def CLIadd(finances, args):
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
    add(finances, title, loc, date, src, acct, cost, note)

# show last x transactions based on criteria
def CLIshowHistory(finances, args):
    # limit of transactions
    count = 5
    if 1 in args:
        count = int(args[1])

    # optional arguments
    acct        = getOpArg(args, 'acct')
    end         = getOpArg(args, 'end')
    start       = getOpArg(args, 'start')
    title       = getOpArg(args, 'title')
    loc         = getOpArg(args, 'loc')
    note        = getOpArg(args, 'note')
    category    = getOpArg(args, 'cat')
    transType   = getOpArg(args, 'transType')
    count       = getOpArg(args, 'count', default=count)

    # get and print results
    results, total = showHistory(finances, count, acct, start, end, title, loc, note, category, transType)
    print(results)
    print('Total:', total)
    return results

# display the progress of a category goal in the current month
def CLIgoalProgress(finances, args):
    if 1 in args:
        # get category and month
        catName = args[1]
        month = ''
        year = ''
        if 2 in args:
            month = args[2]
        if 3 in args:
            year = args[3]

        # fetch progress for month
        first, last, month, igoal, spent, sgoal, progress = goalProgress(finances, catName, month, year)

        # print results
        print(catName, 'from', first, 'to', last)
        print(month)
        if igoal > 0:
            print(tabulate([['Spent', spent], ['Goal', sgoal], ['Progress', progress + '%']]))
        else:
            print('Spent:', spent)
    else:
        print('Requires at least 1 argument, the name of the category.')

# display the progress of a category goal in the current month
def CLImonthlyGoal(finances, args):
    if 1 in args:
        # get parameters
        catName = args[1]
        plot = getOpArg(args, 'plot', default=False)
        months = 6
        if 2 in args:
            months = int(args[2])

        dates, spents, goals, progresses = monthlyGoal(finances, catName, months)
        print(tabulate([dates, spents, goals, progresses]))
        if plot:
            plt.show()
    else:
        print('Requires at least 1 argument, the name of the category.')

# list all accounts
def CLIlistAccounts(finances, args):
    print('Current accounts:')
    print('\n'.join(finances.accounts))

# list all accounts
def CLIlistCategories(finances, args):
    print('Current categories:')
    print('\n'.join(finances.categories))

# add a new acount
def CLIaddAccount(finances, args):
    # prompt if name is not provided
    if 1 in args:
        newAcct = args[1]
    else:
        newAcct = input('New account: ')

    # save
    success = addAccount(finances, newAcct)

# add a new category
def CLIaddCategory(finances, args):
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

    name = addCategory(finances, name, goal, titles, locs, accts)

# get basic info about an account
def CLIaccountInfo(finances, args):
    # check account name
    if 1 not in args:
        print('An account name is required')
        return
    acct = correctFormat(finances, 'account', args[1])

    # get optional arguments
    start = getOpArg(args, 'start')
    end   = getOpArg(args, 'end')
    reach = getOpArg(args, 'months', 6)

    # request data
    rows, toTrans, fromTrans, add, sub, delta = accountInfo(finances, acct, start, end, reach)

    # print title
    title = acct + ' Stats:'
    print(title)
    print('-'*len(title))

    # fetch lasunkmonths and print
    if reach !=unk:
        print(tunkate(rows, headers=['Month', 'Delta']), '\n')

    print(tabulate([['Count', toTrans, fromTrans], ['Value', add, sub]], headers=['', 'In', 'Out']))
    print('\n\u001b[1mNet Total:', delta)

# get balances of all accounts and total
def CLIbalance(finances, args):
    balances = balance(finances)
    longestName = 0
    longestCost = 0
    # get each accounts balance and process
    for acct in balances:
        if len(acct) > longestName:
            longestName = len(acct)
        valStr = balances[acct]
        dStr = valStr[:str(valStr).index('.')]
        if len(dStr) > longestCost:
            longestCost = len(dStr)

    # display info
    print('Current Balances:')
    print('-----------------')
    for acct in balances:
        name = acct
        delta = balances[acct]
        dStr = delta[:str(delta).index('.')]
        spaces = 1 + (longestName - len(name)) + (longestCost - len(dStr))
        if name == 'Total':
            name = '\u001b[1mTotal'
        print(name, ':', ' '*spaces, delta, sep='')

# exports data to a csv file
def CLIexport(finances, args):
    if 1 in args:
        fileLoc = args[1]

        # optional arguments
        acct        = 'account', getOpArg(args, 'acct')
        end         = 'date', getOpArg(args, 'end')
        start       = 'date', getOpArg(args, 'start')
        title       = 'title', getOpArg(args, 'title')
        loc         = 'location', getOpArg(args, 'loc')
        note        = 'note', getOpArg(args, 'note')
        transType   = getOpArg(args, 'transType').lower()
        
        # fetch items to export
        count = export(finances, fileLoc, acct, start, end, title, loc, note, transType)
        print('Exported', count, 'items to', fileLoc)
    else:
        print('Requires at least 1 argument, the file location')

# plot historical values
def CLIvisualHistory(finances, args):
    visualHistory(finances, CLIshowHistory(finances, args))
    plt.show()

# show unique values in a given column
def CLIunique(finances, args):
    if 1 in args:
        unique = unique(finances, args[1])
        if unique:
            print(unique)
        else:
            print('Column not found please choose from:', ', '.join(finances.log.columns))
    else:
        print('Requires 1 argument, the column name')

# replace all matching values in column
def CLIreplaceAll(finances, args):
    if 3 in args:
        if not replaceAll(finances, args[1], args[2], args[3]):
            print('Column not found please choose from:', ', '.join(finances.log.columns))
    else:
        print('Requires 3 arguments, the column name, find string, and replace string')

# command to edit a value in a column
def CLIedit(finances, args):
    if 3 in args:
        if not edit(finances, args[1], args[2], args[3]):
            print('Column not found please choose from:', ', '.join(finances.log.columns))
    else:
        print('Please provide a row number and column name')

# plot an account's value over time
def CLIplot(finances, args):
    # get unit of time, default is days
    units = 'days'
    if 1 in args:
        units = args[1]
    units = units.lower()

    # get optional arguments
    acct        = getOpArg(args, 'acct')
    start       = getOpArg(args, 'start')
    end         = getOpArg(args, 'end')
    invert      = getOpArg(args, 'invert', default=False)
    points      = getOpArg(args, 'dots', default=False)
    noLine      = getOpArg(args, 'noline', default=False)
    allPoints   = getOpArg(args, 'alldays', default=False)
    totals      = getOpArg(args, 'totals', default=False)

    plot(finances, units, acct, start, end, invert, points, noLine, allPoints, totals)
    plt.show()

# reset the configuration
def CLIreset(finances, args):
    confirm = input('Are you sure you want to delete everything? [y/N] ')
    if reset(finances, confirm):
        print('Reset complete')

# give help output
def CLIhelpCmd(finances, args):
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
def unknown(finances, args):
    print('Invalid command,', args['cmd'])

# dictionary of commands  
cmds = dict({
    'acctInfo': (CLIaccountInfo, 'Display a brief summary of a given account.', 'acctInfo account [--start start_date] [--end end_date] [--months months_back]'),
    'add': (CLIadd, 'Add a new item to the log.', 'add title@location account amount [--date date] [--note note]'),
    'balance': (CLIbalance, 'Provide the balance of all accounts, as well as the total.', 'balance'),
    'bal': (CLIbalance, 'Shorter form of the balance command.', 'bal'),
    'delete': (CLIdelete, 'Remove an entry from the log.', 'delete entry_index'),
    'del': (CLIdelete, 'Shorter form of the delete command.', 'del entry_index'),
    'edit': (CLIedit, 'Edit a given value in an entry.', 'edit entry_index column'),
    'export': (CLIexport, 'Export entries to a new file.', 'export log_file'),
    'help': (CLIhelpCmd, 'List and describe all command options.', 'help [command]'),
    'history': (CLIshowHistory, 'Display the last X items, default is 5.', 'history [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'hist': (CLIshowHistory, 'Shorter form of the history command.', 'hist [count] [--start start_date] [--end end_date] [--acct account] [--cat category] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'listAccts': (CLIlistAccounts, 'List all known accounts.', 'listAccts'),
    'listCats': (CLIlistCategories, 'List all known categories.', 'listCats'),
    'newAcct': (CLIaddAccount, 'Add a new account.', 'newAcct account_name'),
    'newCat': (CLIaddCategory, 'Add a new category.', 'newCat category_name'),
    'plot': (CLIplot, 'Plot total value per day/month over time.', 'plot [units] [--start start_date] [--end end_date] [--acct account] [-invert] [-dots] [-noline] [-alldays] [-totals]'),
    'progress': (CLIgoalProgress, 'Display current monthly progress of a category goal.', 'progress category_name [month_num] [year_num]'),
    'progressMonths': (CLImonthlyGoal, 'Display goal results over the last few months.', 'progressMonths category_name [num_months] [-plot]'),
    'replace': (CLIreplaceAll, 'Replace all matching strings in a given column.', 'replace column find replace_with'),
    'reset': (CLIreset, 'Resets the existing configuration.', 'reset'),
    'unique': (CLIunique, 'Gets all unique values in a given column.', 'unique column'),
    'visualHistory': (CLIvisualHistory, 'Display the last X items as a plot, default is 5.', 'visualHistory [count] [--start start_date] [--end end_date] [--cat category] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]'),
    'vhist': (CLIvisualHistory, 'Shorter form of the visualHistory command.', 'vhist [count] [--start start_date] [--end end_date] [--acct account] [--title title] [--loc location] [--note note] [--transType to/from/transfer] [--count count]')
})