import os
import pandas as pd
import numpy as np
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
        val = args[arg]
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

# Gets the total for an account per day/month
def totalsPerUnitTime(log, units, acct='', start='', end=''):
    # get appropriate data and split into to and from
    logs = filter(log, acct=acct, start=start, end=end)
    if acct:
        toAcct = logs[logs['to'] == acct]
        fromAcct = logs[logs['from'] == acct]
    else:
        toAcct = logs[logs['to'] != '-']
        fromAcct = logs[logs['from'] != '-']

    # sum into the requested units
    if units.startswith('day'):
        toCounts = toAcct.groupby(pd.to_datetime(toAcct['date']).dt.date).agg({'amount': 'sum'})
        fromCounts = fromAcct.groupby(pd.to_datetime(fromAcct['date']).dt.date).agg({'amount': 'sum'})
    elif units.startswith('week'):
        toCounts = toAcct.groupby(pd.to_datetime(toAcct['date']).dt.week).agg({'amount': 'sum'})
        fromCounts = fromAcct.groupby(pd.to_datetime(fromAcct['date']).dt.week).agg({'amount': 'sum'})
    elif units.startswith('month'):
        toCounts = toAcct.groupby(pd.to_datetime(toAcct['date']).dt.month).agg({'amount': 'sum'})
        fromCounts = fromAcct.groupby(pd.to_datetime(fromAcct['date']).dt.month).agg({'amount': 'sum'})
    elif units.startswith('quarter'):
        toCounts = toAcct.groupby(pd.to_datetime(toAcct['date']).dt.quarter).agg({'amount': 'sum'})
        fromCounts = fromAcct.groupby(pd.to_datetime(fromAcct['date']).dt.quarter).agg({'amount': 'sum'})
    elif units.startswith('year'):
        toCounts = toAcct.groupby(pd.to_datetime(toAcct['date']).dt.year).agg({'amount': 'sum'})
        fromCounts = fromAcct.groupby(pd.to_datetime(fromAcct['date']).dt.year).agg({'amount': 'sum'})
    else:
        print('Unit of', units, 'not found, please use \"days\", \"weeks\", \"months\", or \"quarters\"')
        return pd.Series([])

    # subtract the froms from the tos
    results = toCounts['amount'].sub(fromCounts['amount'], fill_value=0.0)

    # account for the total at the start
    if start:
        baseline = totalAt(log, start, acct=acct)
        results[0] = results[0] + baseline
    
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