import os
import pandas as pd
import numpy as np
from datetime import datetime as dt
from calendar import monthrange

#
# Helper Functions
#

dateFormat = '%Y-%m-%d'

class Finances:
    def __init__(self, confDir, accounts, categories, log):
        self.confDir = confDir
        self.acctFile = confDir + 'accounts.csv'
        self.catFile = confDir + 'categories.csv'
        self.logFile = confDir + 'log.csv'
        self.accounts = accounts
        self.categories = categories
        self.log = log

# Load in necessary data
def load(argDict={}):
    # use default or provided config file
    confDir = '~/.config/finance'
    if 'config' in argDict:
        confDir = argDict['config']
    confDir = os.path.expanduser(confDir)

    if confDir[-1] != '/':
        confDir += '/'

    acctFile = confDir + 'accounts.csv'
    catFile = confDir + 'categories.csv'
    logFile = confDir + 'log.csv'

    # create config file if they don't exist
    try:
        if not os.path.exists(confDir):
            choice = input('No configuration exists. Would you like to link to an existing configuration directory? [y/N] ')
            if choice.lower() == 'y':
                to = input('Where is the existing directory: ')
                to = os.path.expanduser(to)
                os.symlink(to, confDir[:-1])
                link = True
            else:
                print('Creating new configuration...')
                os.makedirs(confDir)

        if not os.path.exists(acctFile):
            setupAccts(acctFile)
    except EOFError as e:
        print(e)
        print('Creating new configuration...')
        os.makedirs(confDir)
        setupAccts(acctFile, accounts=['CASH'])

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
            if len(parts) == 5:
                name = parts[0]
                goal = parts[1]
                titles = parts[2].split(':')
                if len(titles) == 1 and titles[0] == '':
                    titles = []
                locs = parts[3].split(':')
                if len(locs) == 1 and locs[0] == '':
                    locs = []
                accts = parts[4].split(':')
                if len(accts) == 1 and accts[0] == '':
                    accts = []
                categories[name] = [goal, titles, locs, accts]

    log = pd.read_csv(logFile, sep=',', header=0, parse_dates=['date'])[['title', 'location', 'date', 'from', 'to', 'amount', 'note']]
    return Finances(confDir, accounts, categories, log)

# Prompt for creating list of accounts
def setupAccts(acctFile, accounts=[]):
    if not accounts:
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
def getLast(finances, count, acct='', start='', end='', title='', location='', note='', transType='', category=''):
    hLog = filter(finances, acct=acct, start=start, end=end, title=title, location=location, note=note, transType=transType, category=category)
    return hLog.sort_values('date').tail(count)

# Filter the database
def filter(finances, acct='', start='', end='', title='', location='', note='', transType='', category=''):
    hLog = finances.log.copy()
    if acct != '':
        hLog = hLog[(hLog['from'] == acct) | (hLog['to'] == acct)]
    if start != '':
        hLog = hLog[hLog['date'] >= dt.strptime(start, dateFormat)]
    if end != '':
        hLog = hLog[hLog['date'] < dt.strptime(end, dateFormat)]
    if title != '':
        hLog = hLog[hLog['title'].str.contains(title, case=False)]
    if location != '':
        hLog = hLog[hLog['location'].str.contains(location, case=False)]
    if note != '':
        hLog = hLog[hLog['note'].str.contains(note, case=False)]
    if category != '':
        hLog = hLog[hLog.apply(lambda row: determineCategory(row, finances.categories), axis=1) == category]
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
def getAccountInfo(finances, account, start='', end=''):
    cLog = finances.log.copy()

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
def totalsPerUnitTime(finances, units, acct='', start='', end='', category=''):
    # get appropriate data and split into to and from
    logs = filter(finances, acct=acct, start=start, end=end, category=category)
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
        baseline = totalAt(finances, start, acct=acct)
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

# get the progress of a category goal for a month
def getMonthProgress(finances, catName, month, year):
    first = dt(year, month, 1).strftime(dateFormat)
    last = dt(year, month, monthrange(year, month)[1]).strftime(dateFormat)
    month = filter(finances, start=first, end=last, category=catName)
    monthTo = month[month['from'] == '-']
    monthFrom = month[month['to'] == '-']
    spent = -(monthTo['amount'].sum() - monthFrom['amount'].sum())
    goal = finances.categories[catName][0]
    progress = 0
    if goal != '':
        goal = correctFormat(finances, 'amount', goal)
        progress = round(100 * (spent / goal), 2)
    else:
        goal = 0
    return month, first, last, spent, goal, progress

# Gets the total for an account at a date
def totalAt(finances, date, acct=''):
    # get appropriate data and split into to and from
    logs = filter(finances, acct=acct, end=date)
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
    if value == 0:
        return '$0.00'
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

def addEntry(finances, title, loc, date, src, to, amount, note=''):
    # create the row
    finances.log.loc[finances.log.shape[0]] = [title, loc, date, src, to, amount, note]
    return True

def editEntry(finances, row, title, loc, date, src, to, amount, note=''):
    # create the row
    finances.log.loc[row] = [title, loc, date, src, to, amount, note]
    return True
    
# checks that a cell is formatted correctly
def correctFormat(finances, column, value, new=False):
    value = value.strip()
    if value == '' and not new:
        return value
    elif value == '':
        raise Exception('{} must not be empty.'.format(column))
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
            if not new and not value in finances.accounts:
                raise Exception('Account, {}, does not exist in {}.'.format(value, finances.accounts))
            for c in value:
                if not c.isalpha():
                    raise Exception('Account name must consist only of letters. {} found.'.format(c))
        return value
    elif column == 'category':
        # to and from must be a valid category and upper case
        value = value.upper()
        if value != '-':
            if not new and not value in finances.categories:
                raise Exception('Category, {}, does not exist in {}.'.format(value, list(finances.categories.keys())))
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
        titles = category[1]
        locations = category[2]
        accounts = category[3]
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
    ext = os.path.splitext(file)[1]
    if ext == '.csv':
        log.to_csv(file, index=False)
    elif ext == '.xlsx':
        log.to_excel(file, index=False)
    else:
        return False
    return True

def saveCats(categories, file):
    with open(file, 'w+') as f:
        for catName in categories:
            cat = categories[catName]
            goal    = str(cat[0])
            titles  = cat[1]
            locs    = cat[2]
            accts   = cat[3]
            f.write(catName + ',' + goal + ',' + ':'.join(titles) + ',' + ':'.join(locs) + ',' + ':'.join(accts) + '\n')