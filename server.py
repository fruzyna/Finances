import http.server, re, urllib.parse, sys, dominate
import matplotlib.pyplot as plt

from dominate.tags import *
from control import *
from features import *

HOST = ''
PORT = 8080

def addDefaults(queries, defaults):
    for key in defaults:
        if not key in queries:
            queries[key] = defaults[key]
    return queries

def newQuery(queries):
    query_str = ''
    for item in queries.items():
        key, value = item
        query_str += '&' + key + '=' + value
    return query_str

def createQTextbox(name, queries, size=20, readonly=False):
    return td( input_(type='text', name=name, value=queries[name], size=size, readonly=readonly, style=('background-color: #fcc' if queries['invalid'] == name else '')) )

def createTextbox(name, value, size=20, readonly=False):
    return td( input_(type='text', name=name, value=value, size=size, readonly=readonly) )

def createQNumbox(name, queries, min='0', step='1', size=20, readonly=False):
    return td( input_(type='number', name=name, value=queries[name], min=min, step=step, size=size, readonly=readonly, style=('background-color: #fcc' if queries['invalid'] == name else '')) )

def createNumbox(name, value, min='0', step='1', size=20, readonly=False):
    return td( input_(type='number', name=name, value=str(value), min=min, step=step, size=size, readonly=readonly) )

def createQDropdown(name, form, options, queries):
    return createDropdown(name, form, options, queries[name])

def createDropdown(name, form, options, selected=''):
    dropdown = select(name=name, form=form)
    for value in options:
        op = option(value, selected=(value == selected)) 
        dropdown.add(op)
    return td(dropdown)

def createCheckbox(name, checked, text):
    return td( input_(type='checkbox', name=name, checked=checked), text)

def createSubmit(name):
    return td( input_(type='submit', value=name) )

def WEBbalance(finances, queries, path):
    # balances tab 
    queries = addDefaults(queries, {'edit': ''})

    # create table with header/titles
    body = table(cls='data')
    header = tr(cls='header')
    header.add(td('Account'))
    header.add(td('Balance'))
    body.add(header)
        
    # get each accounts balance and process
    accts = ''
    balances = balance(finances)
    for i, acct in enumerate(balances):
        # add row to balances table
        balRow = tr()
        if queries['edit'] == str(i):
            rename = form(id='rename', action='/rename')
            nameCell = td()
            nameCell.add( input_(type='text', name='oldName', value=acct, hidden=True) )
            nameCell.add( input_(type='text', name='newName', value=acct) )
            rename.add(nameCell)
            rename.add( td(balances[acct]) )
            rename.add( createSubmit('Save') )
            balRow.add(rename)
        else:
            balRow.add( td( a(acct, cls='click', href=path+'?edit='+str(i)) ) )
            balRow.add( td(balances[acct]) )
        body.add(balRow)
    return body

def WEBgoalProgress(finances, queries, path):
    # goals tab
    queries = addDefaults(queries, {'edit': '', 'delete': '', 'month': ''})

    if queries['delete'] != '':
        deleteCat(finances, queries['delete'], 'y')

    body = div()

    # create month form/dropdown
    month = form('Month: ', id='month')
    dropdown = select(name='month', form='month', onchange='this.form.submit()')
    month.add(dropdown)
    body.add(month)

    # create data table
    data = table(cls='data')
    # create table headers/titles
    titles = tr(cls='header')
    titles.add( td('Account') )
    titles.add( td('Goal') )
    titles.add( td('Current') )
    titles.add( td('Progress') )
    titles.add( td('Delete') )
    data.add(titles)
    body.add(data)

    if finances.categories:
        # populate dropdown with months
        monthsStr = ''
        months = finances.log['date'].map(lambda x: str(x.year) + '-' + ('%02d' % x.month)).sort_values(ascending=False).unique()
        for month in months:
            dropdown.add( option(month, value=month, selected=queries['month'] == month) )

        # get month and year from query
        month = year = ''
        if queries['month']:
            year, month = queries['month'].split('-')
            
        # get each accounts balance and process
        cats = ''
        for cat in finances.categories:
            first, last, _, igoal, spent, sgoal, progress = goalProgress(finances, cat, month, year)
            if igoal <= 0:
                progress = 'N/A'
                sgoal = 'No Goal'
            else:
                progress += '%'

            # add row to data table
            goal = tr()
            if queries['edit'] == cat:
                edit = tr()
                edit.add( createTextbox('cat', cat, readonly=True) )
                edit.add( createNumbox('goal', igoal) )
                edit.add( td(spent) )
                edit.add( td(progress) )
                edit.add( createSubmit('Save') )
                goal.add( form(edit, id='editgoal', action='/editgoal') )
            else:
                goal.add( td( a(cat, cls='click', href='/history?cat='+cat) ) )
                goal.add( td( a(sgoal, cls='click', href=path+'?edit='+cat) ) )
                goal.add( td(spent))
                goal.add( td(progress))
                goal.add( td( a('delete', href=path+'?delete='+cat) ) )
            data.add(goal)

        body.add('(from ' + first + ' to ' + last + ')')
        return body
    else:
        return h3('No categories/goals found')

def WEBadd(finances, queries):
    # add tab
    # load in base add section
    queries = addDefaults(queries, {'invalid': '', 'entry_title': '', 'entry_location': '', 'entry_date': dt.today().strftime(dateFormat), \
        'entry_to': '', 'entry_from': '', 'entry_amount': '', 'entry_note': '', 'account_name': '', \
        'category_name': '', 'category_goal': '', 'category_titles': '', 'category_locations': '', 'category_accounts': ''})

    body = div()

    addEntry = div()
    addEntry.add( h2('Add Entry') )
    entry = table()
    entryTop = tr()
    entryTop.add( td('Title:') )
    entryTop.add( createQTextbox('entry_title', queries) )
    entryTop.add( td('Location:') )
    entryTop.add( createQTextbox('entry_location', queries) )
    entry.add(entryTop)
    entryMid = tr()
    entryMid.add( td('From:') )
    entryMid.add( createQDropdown('entry_from', 'entry', [''] + finances.accounts, queries) )
    entryMid.add( td('To:') )
    entryMid.add( createQDropdown('entry_to', 'entry', [''] + finances.accounts, queries) )
    entryMid.add( td('Amount:') )
    entryMid.add( createQNumbox('entry_amount', queries, step='.01') )
    entry.add(entryMid)
    entryBot = tr()
    entryBot.add( td('Date:') )
    entryBot.add( createQTextbox('entry_date', queries, size='10') )
    entryBot.add( td('Note:') )
    entryBot.add( createQTextbox('entry_note', queries) )
    entryBot.add( createSubmit('Log') )
    entry.add(entryBot)
    addEntry.add( form(entry, id='entry', action='/addlog') )
    body.add(addEntry)

    addCat = div()
    addCat.add( h2('Add Category') )
    category = table()
    catTop = tr()
    catTop.add( td('Name:') )
    catTop.add( createQTextbox('category_name', queries) )
    catTop.add( td('Goal:') )
    catTop.add( createQNumbox('category_goal', queries) )
    category.add(catTop)
    catMid = tr()
    catMid.add( td('Titles:') )
    catMid.add( createQTextbox('category_titles', queries) )
    catMid.add( td('Locations:') )
    catMid.add( createQTextbox('category_locations', queries) ) 
    category.add(catMid)
    catBot = tr()
    catBot.add( td('Accounts:') )
    catBot.add( createQTextbox('category_accounts', queries) )
    catBot.add( createSubmit('Create') )
    category.add(catBot)
    addCat.add( form(category, id='cat', action='/addcat') )
    body.add(addCat)

    addAcct = div()
    addAcct.add( h2('Add Account') )
    account = table()
    account.add( td('Name:') )
    account.add( createQTextbox('account_name', queries) )
    account.add( createSubmit('Add') )
    addAcct.add( form(account, id='acct', action='/addacct') )
    body.add(addAcct)

    return body

# TODO catch exceptions
def WEBhistory(finances, queries, path):
    # history tab
    # read queries and create defaults
    queries = addDefaults(queries, {'invalid': '', 'results': '5', 'title': '', 'loc': '', 'acct': '', 'amount': '', 'note': '', 'cat': '', 'start': '', 'end': '', 'transType': '', 'plot': '', 'edit': ''})
    
    # load in base history section
    options = table()

    topRow = tr()
    topRow.add( td('Results:') )
    topRow.add( createQNumbox('results', queries, size='4') )
    topRow.add( td('Title:') )
    topRow.add( createQTextbox('title', queries) )
    topRow.add( td('Location:') )
    topRow.add( createQTextbox('loc', queries) )
    options.add(topRow)

    midRow = tr()
    midRow.add( td('Transfer Type:') )
    midRow.add( createQDropdown('transType', 'hist', ['', 'to', 'from', 'transfer'], queries) )
    midRow.add( td('Account:') )
    midRow.add( createQDropdown('acct', 'hist', [''] + [key for key in finances.accounts], queries) )
    midRow.add( td('Category:') )
    midRow.add( createQDropdown('cat', 'hist', [''] + [key for key in finances.categories], queries) )
    options.add(midRow)

    checked = queries['plot'] == 'on'

    botRow = tr()
    botRow.add( td('Start Date:') )
    botRow.add( createQTextbox('start', queries, size='10') )
    botRow.add( td('EndDate:') )
    botRow.add( createQTextbox('end', queries, size='10') )
    botRow.add( createCheckbox('plot', checked, 'Plot?') )
    botRow.add( createSubmit('Search') )
    options.add(botRow)

    # search database
    results, _ = showHistory(finances, queries['results'], queries['acct'], queries['start'], queries['end'], queries['title'], queries['loc'], queries['note'], queries['cat'], queries['transType'])
    
    # create table for results
    history = table(cls='data')
    # place column names in table
    header = tr(cls='header')
    header.add( td('row') )
    for col in results.columns:
        header.add( td(col) )
    header.add( td('edit') )
    history.add(header)
    
    # build each row of results in table
    rows = ''
    for i, row in results.iterrows():
        i = str(i)
        entry = tr()
        if i == queries['edit']:
            edit = form(id='edit', action='/edit')
            edit.add( createNumbox('row', i, size='3', readonly=True) )
            edit.add( createTextbox('title', str(row['title'])) )
            edit.add( createTextbox('location', str(row['location'])) )
            edit.add( createTextbox('date', str(row['date']).split(' ')[0]) )
            edit.add( createQDropdown('from', 'edit', [''] + finances.accounts, queries) )
            edit.add( createQDropdown('to', 'edit', [''] + finances.accounts, queries) )
            edit.add( createNumbox('amount', str(row['amount']), min='0', step='.01') )
            edit.add( createTextbox('note', str(row['note'])) )
            edit.add( createSubmit('Save') )
        else:
            entry.add( td(str(i)) )
            for value in row:
                entry.add( td(str(value)) )
            entry.add( td( a('edit', href=path+'?edit='+i), a('delete', href='/delete?row='+i) ) )
        history.add(entry)

    if queries['plot'] == 'on':
        visualHistory(finances, results)
        plt.savefig('vhist.png')
        #text += '<img src="vhist.png">'

    body = div()
    body.add(form(options, id='hist'))
    body.add(history)
    return body

def WEBplot(finances, queries):
    # plot tab
    # read queries and create defaults
    queries = addDefaults(queries, {'invalid': '', 'units': 'days', 'acct': '', 'start': '', 'end': '', 'invert': '', 'points': '', 'noLine': '', 'allPoints': '', 'totals': ''})
    
    options = table(id='plot')

    # add row for dropdowns
    selects = tr()
    selects.add( td('Units:') )
    selects.add( createQDropdown('units', 'plot-ops', ['days', 'weeks', 'months', 'quarters', 'years'], queries) )
    selects.add( td('Account:') )
    selects.add( createQDropdown('acct', 'plot-ops', [''] + finances.accounts, queries) )
    options.add(selects)

    # add row for dates
    dates = tr()
    dates.add( td('Start Date:') )
    dates.add( createQTextbox('start', queries, size=10) )
    dates.add( td( 'End Date:') )
    dates.add( createQTextbox('end', queries, size=10) )
    options.add(dates)

    # check states of checks
    invert = queries['invert'] == 'on'
    points = queries['points'] == 'on'
    noLine = queries['noLine'] == 'on'
    totals = queries['totals'] == 'on'
    allPoints = queries['allPoints'] == 'on'

    # add row of checkboxes
    checks = tr()
    checks.add( createCheckbox('invert', invert, 'Invert Y-Axis') )
    checks.add( createCheckbox('points', points, 'Show Points') )
    checks.add( createCheckbox('noLine', noLine, 'Hide Line') )
    checks.add( createCheckbox('allPoints', allPoints, 'Plot All Dates') )
    checks.add( createCheckbox('totals', totals, 'Unit Totals') )
    checks.add( createSubmit('Search') )
    options.add(checks)

    # search database
    plot(finances, queries['units'], queries['acct'], queries['start'], queries['end'], invert, points, noLine, allPoints, totals)
    plt.savefig('plot.png')

    # wrap with form and add image
    body = form(options, id='plot-ops')
    body.add( img(src='plot.png') )
    return body

def WEBedit(finances, queries):
    queries = addDefaults(queries, {'title': '', 'location': '', 'date': dt.today().strftime(dateFormat), 'to': '', 'from': '', 'amount': '', 'note': '', 'row': ''})
    editWhole(finances, queries['row'], queries['title'], queries['location'], queries['date'], queries['from'], queries['to'], queries['amount'], queries['note'])

    redirect = meta(content='0; URL=\'/balance\'')
    redirect['http-equiv'] = 'refresh'
    return redirect

def WEBrename(finances, queries):
    queries = addDefaults(queries, {'oldName': '', 'newName': ''})
    renameAccount(finances, queries['oldName'], queries['newName'])

    redirect = meta(content='0; URL=\'/balance\'')
    redirect['http-equiv'] = 'refresh'
    return redirect

def WEBdelete(finances, queries):
    queries = addDefaults(queries, {'row': ''})
    delete(finances, queries['row'], 'y')

    redirect = meta(content='0; URL=\'/history\'')
    redirect['http-equiv'] = 'refresh'
    return redirect

def WEBaddEntry(finances, queries):
    # request to create a new log entry
    # read queries and create defaults
    queries = addDefaults(queries, {'entry_title': '', 'entry_location': '', 'entry_date': dt.today().strftime(dateFormat), 'entry_to': '', 'entry_from': '', 'entry_amount': '', 'entry_note': ''})

    try:
        # create the row and save to file
        addEntry(finances, queries['entry_title'], queries['entry_location'], queries['entry_date'], queries['entry_from'], queries['entry_to'], queries['entry_amount'], queries['entry_note'])

        # redirect to a history page showing the last entry (may not be the new one)
        redirect = meta(content='0; URL=\'/history?results=1\'')
        redirect['http-equiv'] = 'refresh'
        return redirect
    except FormatException as e:
        # go back if there was an error
        redirect = meta(content='0; URL=\'/add?invalid=entry_' + e.column + newQuery(queries) + '\'')
        redirect['http-equiv'] = 'refresh'
        return redirect

def WEBaddAccount(finances, queries):
    # request to create a new account
    # read queries and create defaults
    queries = addDefaults(queries, {'account_name': ''})

    try:
        addAccount(finances, queries['account_name'])
            
        # redirect to the balances page
        redirect = meta(content='0; URL=\'/balance\'')
        redirect['http-equiv'] = 'refresh'
        return redirect
    except FormatException as e:
        # go back if there was an error
        redirect = meta(content='0; URL=\'/add?invalid=account_name&account_name=' + queries['account_name'] +  '\'')
        redirect['http-equiv'] = 'refresh'
        return redirect

def WEBaddCategory(finances, queries):
    # request to create a new category
    # read queries and create defaults
    queries = addDefaults(queries, {'category_name': '', 'category_goal': '', 'category_titles': '', 'category_locations': '', 'category_accounts': ''})

    try:
        name = addCategory(finances, queries['category_name'], queries['category_goal'], queries['category_titles'], queries['category_locations'], queries['category_accounts'])

        # redirect to a history page of the category
        redirect = meta(content='0; URL=\'/history?cat=' + name + '\'')
        redirect['http-equiv'] = 'refresh'
        return redirect
    except FormatException as e:
        # go back if there was an error
        redirect = meta(content='0; URL=\'/add?invalid=category_' + e.column + newQuery(queries) + '\'')
        redirect['http-equiv'] = 'refresh'
        return redirect

def WEBeditGoal(finances, queries):
    # edit goal response
    queries = addDefaults(queries, {'cat': '', 'goal': ''})
    editGoal(finances, queries['cat'], queries['goal'])

    redirect = meta(content='0; URL=\'/goals\'')
    redirect['http-equiv'] = 'refresh'
    return redirect

class requestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        # generate the web page
        path = urllib.parse.unquote_plus(self.path)
        if path.endswith('.png'):
            with open(self.path[1:], 'rb') as f:
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                self.wfile.write(f.read())
        else:
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            text = self.generate_page()
            self.wfile.write(bytes(text, 'utf8'))
        return

    # generate web page based off url and queries
    def generate_page(self):
        # load in finance data
        finances = load(noSetup=noSetup)

        # core page
        page = dominate.document(title='Finances')
        #page.head.add(link(rel='stylesheet', href='style.css'))
        with open('style.css', 'r') as f:
            page.head.add(style(f.read()))

        # main table
        ttable = table(id='layout', cellspacing='0')
        page.add(ttable)

        # top table row
        headerRow = tr()
        headerRow.add( td( h1('Finances'), id='title' ) )
        ttable.add(headerRow)

        # bottom table row
        bodyRow = tr()
        ttable.add(bodyRow)

        # left menu cell
        menuCell = td(id='options')
        menuCell.add( a('Balances', href='/balance', cls='option') )
        menuCell.add( a('Goals', href='/goals', cls='option') )
        menuCell.add( a('Add', href='/add', cls='option') )
        menuCell.add( a('History', href='/history', cls='option') )
        menuCell.add( a('Plot', href='/plot', cls='option') )
        bodyRow.add(menuCell)

        # remove encoding from url
        path = urllib.parse.unquote_plus(self.path)
        queries = {}
        queryStrs = re.findall('([A-z0-9]+=[^&?]+)', path)
        for q in queryStrs:
            key, val = q.split('=')
            if key[-1] == '?':
                key = key[:-1]
            queries[key] = val
        
        # right body cell
        body = div()
        pageName = ''
        if path.startswith('/history'):
            pageName = 'History'
            body = WEBhistory(finances, queries, path)
        elif path.startswith('/addlog'):
            body = WEBaddEntry(finances, queries)
        elif path.startswith('/addacct'):
            body = WEBaddAccount(finances, queries)
        elif path.startswith('/addcat'):
            body = WEBaddCategory(finances, queries)
        elif path.startswith('/add'):
            pageName = 'Add'
            body = WEBadd(finances, queries)
        elif path.startswith('/plot'):
            pageName = 'Plot'
            body = WEBplot(finances, queries)
        elif path.startswith('/goals'):
            pageName = 'Goals'
            body = WEBgoalProgress(finances, queries, path)
        elif path.startswith('/editgoal'):
            body = WEBeditGoal(finances, queries)
        elif path.startswith('/edit'):
            body = WEBedit(finances, queries)
        elif path.startswith('/rename'):
            body = WEBrename(finances, queries)
        elif path.startswith('/delete'):
            body = WEBdelete(finances, queries)
        elif path.startswith('/style.css'):
            with open('style.css', 'r') as f:
                return f.read()
        else:
            pageName = 'Balances'
            body = WEBbalance(finances, queries, path)
            
        headerRow.add( td( h2(pageName, id='pageName'), id='header') )
        bodyRow.add( td(body, id='content') )

        return str(page)

noSetup = False
if len(sys.argv) > 1:
    if sys.argv[1] == 'auto':
        print("NO SETUP MODE ENABLED")
        noSetup = True

# start server
with http.server.HTTPServer((HOST, PORT), requestHandler) as httpd:
    print('Running server at http://localhost:' + str(PORT))
    httpd.serve_forever()