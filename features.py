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
def delete(finances, row, confirm):
    i = int(row)
    if confirm.lower() == 'y':
        log = finances.log.drop(i)
        save(log, finances.logFile)
        return True
    else:
        return False

# command to add a new transation
def add(finances, title, loc, date, src, to, amount, note):
    if src == '' and to == '':
        return False
    elif src == '':
        src = '-'
    elif to == '':
        to = '-'

    if date == '':
        date = dt.today().strftime(dateFormat)

    title   = correctFormat(finances, 'title', title, new=True)
    loc     = correctFormat(finances, 'location', loc, new=True)
    date    = correctFormat(finances, 'date', date)
    src     = correctFormat(finances, 'from', src)
    to      = correctFormat(finances, 'to', to)
    amount  = correctFormat(finances, 'amount', amount)
    note    = correctFormat(finances, 'note', note)

    # add to log and save
    addEntry(finances, title, loc, date, src, to, amount, note)
    save(finances.log, finances.logFile)
    return True

# command to add a new transation
def editWhole(finances, row, title, loc, date, src, to, amount, note):
    if src == '' and to == '':
        return False
    elif src == '':
        src = '-'
    elif to == '':
        to = '-'

    if date == '':
        date = dt.today().strftime(dateFormat)

    title   = correctFormat(finances, 'title', title, new=True)
    loc     = correctFormat(finances, 'location', loc, new=True)
    date    = correctFormat(finances, 'date', date)
    src     = correctFormat(finances, 'from', src)
    to      = correctFormat(finances, 'to', to)
    amount  = correctFormat(finances, 'amount', amount)
    note    = correctFormat(finances, 'note', note)
    row     = int(row)

    # add to log and save
    editEntry(finances, row, title, loc, date, src, to, amount, note)
    save(finances.log, finances.logFile)
    return True

# command to add a new transation
def renameAccount(finances, oldName, newName):
    # check account names
    oldName = correctFormat(finances, 'account', oldName, new=False)
    newName = correctFormat(finances, 'account', newName, new=True)

    usages = filter(finances, acct=oldName)
    for index, row in usages.iterrows():
        src = row['from']
        if src == oldName:
            src = newName
        to = row['to']
        if to == oldName:
            to = newName
        editEntry(finances, index, row['title'], row['location'], row['date'], src, to, row['amount'], row['note'])

    for i, name in enumerate(finances.accounts):
        if name == oldName:
            finances.accounts[i] = newName

    save(finances.log, finances.logFile)
    with open(finances.acctFile, 'w+') as f:
        f.write(','.join(finances.accounts))
    return True

# show last x transactions based on criteria
def showHistory(finances, count, acct, start, end, title, loc, note, category, transType):
    # optional arguments
    count = int(count)
    if count < 1:
        count = 1
    acct        = correctFormat(finances, 'account', acct)
    start       = correctFormat(finances, 'date', start)
    end         = correctFormat(finances, 'date', end)
    title       = correctFormat(finances, 'title', title)
    loc         = correctFormat(finances, 'location', loc)
    note        = correctFormat(finances, 'note', note)
    category    = correctFormat(finances, 'category', category)
    if not transType in ['', 'to', 'from', 'transfer']:
        raise Exception('Invalid transfer type {}.'.format(transType))

    # get and print results
    results = getLast(finances, count, acct=acct, start=start, end=end, title=title, location=loc, note=note, transType=transType, category=category)
    return results, valueToString(results['amount'].sum())

# display the progress of a category goal in the current month
def goalProgress(finances, catName, month, year):
    catName = correctFormat(finances, 'category', catName)
    today = dt.today()
    if month != '':
        today = today.replace(month=int(month))
    if year != '':
        today = today.replace(year=int(year))

    # fetch progress for month
    month, first, last, spent, goal, progress = getMonthProgress(finances, catName, today.month, today.year)
    if progress == 0:
        progress = '0'
    else:
        progress = str(progress)
    return first, last, month, goal, valueToString(spent), valueToString(goal), progress

# display the progress of a category goal in the current month
def monthlyGoal(finances, catName, months):
    # get parameters
    catName = correctFormat(finances, 'category', catName)
    months = int(months)

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
        _, first, _, spent, goal, progress = getMonthProgress(finances, catName, m, y)

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

    return dates, spents, goals, progresses

# add a new acount
def addAccount(finances, newAcct):
    newAcct = correctFormat(finances, 'account', newAcct, new=True)

    # write to file
    finances.accounts.append(newAcct)
    with open(finances.acctFile, 'w+') as f:
        f.write(','.join(finances.accounts))
    return True

# add a new category
def addCategory(finances, name, goal, titles, locs, accts):
    name    = correctFormat(finances, 'category', name, new=True)
    goal    = correctFormat(finances, 'amount', goal)
    titles  = [correctFormat(finances, 'title', title) for title in titles.split(',')]
    locs    = [correctFormat(finances, 'location', loc) for loc in locs.split(',')]
    accts   = [correctFormat(finances, 'account', acct) for acct in accts.split(',')]

    # write to file
    categories = finances.categories
    categories[name] = [goal, titles, locs, accts]
    with open(finances.catFile, 'w+') as f:
        for catName in categories:
            cat = categories[catName]
            goal    = str(cat[0])
            titles  = cat[1]
            locs    = cat[2]
            accts   = cat[3]
            f.write(catName + ',' + goal + ',' + ':'.join(titles) + ',' + ':'.join(locs) + ',' + ':'.join(accts) + '\n')
    return name

# get basic info about an account
def accountInfo(finances, acct, start, end, reach):
    acct = correctFormat(finances, 'account', acct)

    # get optional arguments
    starting = correctFormat(finances, 'date', start)
    ending   = correctFormat(finances, 'date', end)
    reach    = -int(reach)

    # request data
    results = totalsPerUnitTime(finances, 'months', acct=acct, start=starting, end=ending)

    # fetch last 6 months and print
    rows = []
    if reach != '0':
        for month, amount in results.iteritems():
            rows.append([month, valueToString(amount)])
        rows = rows[reach:]

    add, sub, delta, toTrans, fromTrans, trans = getAccountInfo(finances, acct, starting, ending)
    return rows, toTrans, fromTrans, valueToString(add), valueToString(sub), valueToString(delta)

# get balances of all accounts and total
def balance(finances):
    total = 0
    accts = {}
    # get each accounts balance and process
    for acct in finances.accounts:
        _,_, delta, _,_,_ = getAccountInfo(finances, acct)
        valStr = valueToString(delta)
        dStr = valStr[:str(valStr).index('.')]
        accts[acct] = valStr
        total += delta
    accts['Total'] = valueToString(total)
    return accts

# exports data to a csv file
def export(finances, fileLoc, acct, start, end, title, loc, note, transType):
    fileLoc = os.path.expanduser(fileLoc)
    if not fileLoc.endswith('.csv'):
        fileLoc += '.csv'

    # optional arguments
    acct        = correctFormat(finances, 'account', acct)
    start       = correctFormat(finances, 'date', start)
    end         = correctFormat(finances, 'date', end)
    title       = correctFormat(finances, 'title', title)
    loc         = correctFormat(finances, 'location', loc)
    note        = correctFormat(finances, 'note', note)
    if not transType in ['to', 'from', 'transfer']:
        raise Exception('Invalid transfer type.')
    
    # fetch items to export
    items = filter(finances, acct=acct, start=start, end=end, title=title, location=loc, note=note, transType=transType)
    save(items, fileLoc)
    return items.index

# plot historical values
def visualHistory(finances, results):
    fig, ax = plt.subplots()
    ax = results.plot(x='date', y='amount', kind='bar', ax=ax, title='History')
    ax.set_xlabel('Transaction')
    ax.set_ylabel('Absolute Dollars')

# show unique values in a given column
def unique(finances, column):
    if column in finances.log:
        unique = finances.log[column].unique()
        unique.sort()
        return unique
    else:
        return False

# replace all matching values in column
def replaceAll(finances, column, old, new):
    if column in log:
        old = '^' + correctFormat(finances, column, old) + '$'
        new = correctFormat(finances, column, new)
        log = finances.log
        log[column] = log[column].replace({old: new}, regex=True)
        save(log, finances.logFile)
        return True
    else:
        return False

# command to edit a value in a column
def edit(finances, row, column, new):
    i = int(row)
    if column in finances.log:
        log = finances.log
        log.loc[i, column] = correctFormat(finances, column, new)
        save(log, finances.logFile)
        return True
    else:
        return False

# plot an account's value over time
def plot(finances, units, acct, start, end, invert, points, noLine, allPoints, totals):
    units = units.lower()

    # get optional arguments
    acct    = correctFormat(finances, 'account', acct)
    start   = correctFormat(finances, 'date', start)
    end     = correctFormat(finances, 'date', end)

    # request data
    results = totalsPerUnitTime(finances, units, acct=acct, start=start, end=end)

    # give up if request failed
    if results.empty:
        return False

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
        return False

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

# reset the configuration
def reset(finances, confirm):
    if confirm.lower() == 'y':
        confDir = finances.confDir[:-1]
        if os.path.islink(confDir):
            os.unlink(confDir)
        else:
            shutil.rmtree(confDir)
        return True
    else:
        return False