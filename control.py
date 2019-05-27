import os
import pandas as pd
import numpy as np
from datetime import datetime as dt
from decimal import *

#
# Helper Functions
#

dateFormat = '%Y-%m-%d'

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
def setupCats(catFile):
    with open(catFile, 'w+') as f:
        f.write('')

# Initiates log file
def setupLog(logFile):
    with open(logFile, 'w+') as f:
        f.write('index,title,location,date,from,to,amount,note')

# TODO account for new unprocessed dates in date column
# A history/search tool
def getLast(log, count, categories, acct='', start='', end='', title='', location='', note='', transType='', category=''):
    hLog = filter(log, categories, acct=acct, start=start, end=end, title=title, location=location, note=note, transType=transType, category=category)
    return hLog.sort_values('date').tail(count)

# Filter the database
def filter(log, categories, acct='', start='', end='', title='', location='', note='', transType='', category=''):
    hLog = log
    if acct != '':
        hLog = hLog[(hLog['from'] == acct) | (hLog['to'] == acct)]
    if start != '':
        hLog = hLog[hLog['date'] >= dt.strptime(start, dateFormat)]
    if end != '':
        hLog = hLog[hLog['date'] < dt.strptime(end, dateFormat)]
    if title != '':
        hLog = hLog[hLog['title'].str.contains(title)]
    if location != '':
        hLog = hLog[hLog['location'].str.contains(location)]
    if note != '':
        hLog = hLog[hLog['note'].str.contains(note)]
    if category != '':
        hLog = hLog[hLog.apply(lambda row: determineCategory(row, categories), axis=1) == category]
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
        val = args[arg]
    return val

# Gets basic account stats
def getAccountInfo(log, account, start='', end=''):
    cLog = log

    # filter by date (optional)
    if start != '':
        cLog = cLog[cLog['date'] >= dt.strptime(start, dateFormat)]
    if end != '':
        cLog = cLog[cLog['date'] < dt.strptime(end, dateFormat)]

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

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# Gets the total for an account per day/month
def totalsPerUnitTime(log, units, categories, acct='', start='', end='', category=''):
    # get appropriate data and split into to and from
    logs = filter(log, categories, acct=acct, start=start, end=end, category=category)
    if acct:
        toAcct = logs[logs['to'] == acct]
        fromAcct = logs[logs['from'] == acct]
    else:
        toAcct = logs[logs['to'] != '-']
        fromAcct = logs[logs['from'] != '-']

    # sum into the requested units
    toDate = pd.to_datetime(toAcct['date'])
    fromDate = pd.to_datetime(fromAcct['date'])
    if units.startswith('day'):
        groupTo = toDate.dt.date
        groupFrom = fromDate.dt.date
    elif units.startswith('week'):
        groupTo = [toDate.dt.year, toDate.dt.week]
        groupFrom = [fromDate.dt.year, fromDate.dt.week]
    elif units.startswith('month'):
        groupTo = [toDate.dt.year, toDate.dt.month]
        groupFrom = [fromDate.dt.year, fromDate.dt.month]
    elif units.startswith('quarter'):
        groupTo = [toDate.dt.year, toDate.dt.quarter]
        groupFrom = [fromDate.dt.year, fromDate.dt.quarter]
    elif units.startswith('year'):
        groupTo = toDate.dt.year
        groupFrom = fromDate.dt.year
    else:
        print('Unit of', units, 'not found, please use \"days\", \"weeks\", \"months\", or \"quarters\"')
        return pd.Series([])
    toCounts = toAcct.groupby(groupTo).agg({'amount': 'sum'})
    fromCounts = fromAcct.groupby(groupFrom).agg({'amount': 'sum'})

    # subtract the froms from the tos
    results = toCounts['amount'].sub(fromCounts['amount'], fill_value=0.0)

    # account for the total at the start
    if start:
        baseline = totalAt(log, start, acct=acct)
        results[0] = results[0] + baseline

    # replace tuples with human readable dates
    if not (units.startswith('year') or units.startswith('day')):
        rows = []
        for index,_ in results.iteritems():
            year, unit = index
            if units.startswith('week'):
                row = 'Week '
            elif units.startswith('quarter'):
                row = 'Q'

            if units.startswith('month'):
                row = months[unit - 1]
            else:
                row += str(unit)

            row += ' ' + str(year)
            rows.append(row)
        results.index = rows
    
    return results

# Gets the total for an account at a date
def totalAt(log, date, acct=''):
    # get appropriate data and split into to and from
    logs = filter(log, acct=acct, end=date)
    if acct:
        toAcct = logs[logs['to'] == acct]
        fromAcct = logs[logs['from'] == acct]
    else:
        toAcct = logs[logs['to'] != '-']
        fromAcct = logs[logs['from'] != '-']
    
    # subtract the froms from the tos
    return toAcct['amount'].sum() - fromAcct['amount'].sum()

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
    
# checks that a cell is formatted correctly
def correctFormat(column, value, new=False, accounts=[], categories={}):
    value = value.strip()
    if value == '':
        return value
    elif column == 'title' or column == 'location':
        # title and location must be letters, numbers, hyphens, and apostrophes
        for c in value:
            if not c.isalpha() and not c.isdigit() and c != ' ' and c != '-' and c != '\'':
                raise Exception('{} must consist only of letters, numbers, spaces, hyphens, and apostrophes. {} found.'.format(column, c))
        return value
    elif column == 'date':
        # date must be in format YYYY-MM-DD
        value = value.replace('/', '-')
        try:
            dt.strptime(value, dateFormat)
        except ValueError:
            raise Exception('Date must be formatted as YYYY-MM-DD.')
        return value
    elif column == 'from' or column == 'to' or column == 'account':
        # to and from must be a valid account and upper case
        value = value.upper()
        if value != '-':
            if not new and not value in accounts:
                raise Exception('Account, {}, does not exist in {}.'.format(value, accounts))
            for c in value:
                if not c.isalpha():
                    raise Exception('Account name must consist only of letters. {} found.'.format(c))
        return value
    elif column == 'category':
        # to and from must be a valid category and upper case
        value = value.upper()
        if value != '-':
            if not new and not value in categories:
                raise Exception('Category, {}, does not exist in {}.'.format(value, categories))
            for c in value:
                if not c.isalpha():
                    raise Exception('Category name must consist only of letters. {} found.'.format(c))
        return value
    elif column == 'amount':
        # amount must be a positive 2 decimal place number
        if type(value) != 'float':
            value = float(value)
        if value < 0:
            raise Exception('Value name must not be less than zero. {} provided.'.format(value))
        return value
    elif column == 'note':
        # note must be a string
        return value
    else:
        return value

# determines category of entry
def determineCategory(row, categories):
    for catName in categories:
        category = categories[catName]
        titles = category[0]
        locations = category[1]
        accounts = category[2]
        if not row['title'] in titles and len(titles) > 0:
            continue
        if not row['location'] in locations and len(locations) > 0:
            continue
        if not row['to'] in accounts and not row['from'] in accounts and len(accounts) > 0:
            continue
        return catName
    return 'OTHER'

# save a df to a file
def save(log, file):
    log.to_csv(file, index=False)