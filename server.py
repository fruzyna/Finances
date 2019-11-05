import http.server, re, urllib.parse, sys, dominate
import matplotlib.pyplot as plt
from datetime import datetime
from dominate.tags import *

from control import *
from features import *
from server.utils import *

HOST = ''
PORT = 8080
FINANCES_VERSION = '2019-11-05-about'

def WEBbalance(finances, queries, path):
    # balances tab 
    queries = addDefaults(queries, {'invalid': '', 'edit_account': '', 'new_account': ''})

    # create table with header/titles
    body = table(cls='data')
    header = tr(cls='header')
    header.add(td('Account'))
    header.add(td('Balance'))
    body.add(header)
        
    # get each accounts balance and process
    accts = ''
    balances = balance(finances)
    for acct in balances:
        # add row to balances table
        balRow = tr()
        if queries['edit_account'] == acct:
            rename = form(id='rename', action='/rename')
            nameCell = td()
            nameCell.add( input_(type='text', name='edit_account', value=acct, hidden=True) )
            nameCell.add( input_(type='text', name='new_account', value=(queries['new_account'] if queries['new_account'] else acct), style=('background-color: #fcc' if queries['invalid'] == 'new_account' else '')) )
            rename.add(nameCell)
            rename.add( td(balances[acct]) )
            rename.add( createSubmit('Save') )
            balRow.add(rename)
        else:
            balRow.add( td( a(acct, cls='click', href=path+'?edit_account='+acct) ) )
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
                goal.add( td( a(cat, cls='click', href='/history?search_category='+cat) ) )
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
    queries = addDefaults(queries, {'invalid': '', 'entry_title': '', 'entry_location': '', 'entry_date': datetime.today().strftime(dateFormat), \
        'entry_to': '', 'entry_from': '', 'entry_amount': '', 'entry_note': '', 'account_name': '', \
        'category_category': '', 'category_amount': '', 'category_title': '', 'category_location': '', 'category_account': ''})

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
    catTop.add( createQTextbox('category_category', queries) )
    catTop.add( td('Goal:') )
    catTop.add( createQNumbox('category_amount', queries) )
    category.add(catTop)
    catMid = tr()
    catMid.add( td('Titles:') )
    catMid.add( createQTextbox('category_title', queries) )
    catMid.add( td('Locations:') )
    catMid.add( createQTextbox('category_location', queries) ) 
    category.add(catMid)
    catBot = tr()
    catBot.add( td('Accounts:') )
    catBot.add( createQTextbox('category_account', queries) )
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
    queries = addDefaults(queries, {'invalid': '', 'search_results': '5', 'search_title': '', 'search_location': '', 'search_account': '', 'search_amount': '', \
        'search_note': '', 'search_category': '', 'search_start': '', 'search_end': '', 'search_transType': '', 'search_plot': '', 'edit_row': '', \
        'edit_title': '', 'edit_location': '', 'edit_date': '', 'edit_to': '', \
        'edit_from': '', 'edit_amount': '', 'edit_note': '', 'edit_row': ''})
    
    # load in base history section
    options = table()

    # search database
    try:
        results, _ = showHistory(finances, queries['search_results'], queries['search_account'], queries['search_start'], queries['search_end'], \
            queries['search_title'], queries['search_location'], queries['search_note'], queries['search_category'], queries['search_transType'])
    except FormatException as e:
        if e.column == 'date':
            queries['invalid'] = 'search_start'
        else:
            queries['invalid'] = 'search_' + e.column
        results, _ = showHistory(finances, 5, '', '', '', '', '', '', '', '')

    # create top row of search options
    topRow = tr()
    topRow.add( td('Results:') )
    topRow.add( createQNumbox('search_results', queries, size='4') )
    topRow.add( td('Title:') )
    topRow.add( createQTextbox('search_title', queries) )
    topRow.add( td('Location:') )
    topRow.add( createQTextbox('search_location', queries) )
    options.add(topRow)

    # create middle row of search options
    midRow = tr()
    midRow.add( td('Transfer Type:') )
    midRow.add( createQDropdown('search_transType', 'hist', ['', 'to', 'from', 'transfer'], queries) )
    midRow.add( td('Account:') )
    midRow.add( createQDropdown('search_account', 'hist', [''] + [key for key in finances.accounts], queries) )
    midRow.add( td('Category:') )
    midRow.add( createQDropdown('search_category', 'hist', [''] + [key for key in finances.categories], queries) )
    options.add(midRow)

    checked = queries['search_plot'] == 'on'

    # create bottom row of search options
    botRow = tr()
    botRow.add( td('Start Date:') )
    botRow.add( createQTextbox('search_start', queries, size='10') )
    botRow.add( td('EndDate:') )
    botRow.add( createQTextbox('search_end', queries, size='10') )
    botRow.add( createCheckbox('search_plot', checked, 'Plot?') )
    botRow.add( createSubmit('Search') )
    options.add(botRow)

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
        if i == queries['edit_row']:
            # fill query with current values
            for key, value in row.iteritems():
                if queries['edit_' + key] == '':
                    if key == 'date':
                        value = str(value).split(' ')[0]
                    queries['edit_' + key] = value

            edit = form(id='edit', action='/editentry')
            edit.add( createNumbox('edit_row', i, size='3', readonly=True) )
            edit.add( createQTextbox('edit_title', queries) )
            edit.add( createQTextbox('edit_location', queries) )
            edit.add( createQTextbox('edit_date', queries) )
            edit.add( createQDropdown('edit_from', 'edit', [''] + finances.accounts, queries) )
            edit.add( createQDropdown('edit_to', 'edit', [''] + finances.accounts, queries) )
            edit.add( createQNumbox('edit_amount', queries, min='0', step='.01') )
            edit.add( createQTextbox('edit_note', queries) )
            edit.add( createSubmit('Save') )
            entry.add(edit)
        else:
            entry.add( td(str(i)) )
            for value in row:
                entry.add( td(str(value)) )
            editQ = queries.copy()
            editQ['edit_row'] = i
            entry.add( td( a('edit', href='/history' + newQuery(editQ)), a('delete', href='/delete?row='+i) ) )
        history.add(entry)

    if checked:
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

def WEBabout(finances, queries):
    # about tab
    body = div()
    body.add( h2('Finances by Liam Fruzyna') )
    body.add( p('Version: ' + FINANCES_VERSION) )
    body.add( p('2019 Liam Fruzyna, MIT Licensed') )
    body.add( a('View source on GitHub', href='https://github.com/mail929/Finances'))
    return body

def WEBeditEntry(finances, queries):
    queries = addDefaults(queries, {'edit_title': '', 'edit_location': '', 'edit_date': datetime.today().strftime(dateFormat), 'edit_to': '', \
        'edit_from': '', 'edit_amount': '', 'edit_note': '', 'edit_row': ''})

    try:
        editWhole(finances, queries['edit_row'], queries['edit_title'], queries['edit_location'], queries['edit_date'], queries['edit_from'], \
            queries['edit_to'], queries['edit_amount'], queries['edit_note'])

        redirect = meta(content='0; URL=\'/balance\'')
        redirect['http-equiv'] = 'refresh'
        return redirect
    except FormatException as e:
        # go back if there was an error
        redirect = meta(content='0; URL=\'/history?invalid=edit_' + e.column + newQuery(queries) + '\'')
        redirect['http-equiv'] = 'refresh'
        return redirect

def WEBrenameAccount(finances, queries):
    queries = addDefaults(queries, {'edit_account': '', 'new_account': ''})

    try:
        renameAccount(finances, queries['edit_account'], queries['new_account'])

        redirect = meta(content='0; URL=\'/balance\'')
        redirect['http-equiv'] = 'refresh'
        return redirect
    except FormatException as e:
        redirect = meta(content='0; URL=\'/balance?invalid=new_account' + newQuery(queries) + '\'')
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
        redirect = meta(content='0; URL=\'/history?search_results=1&search_title=' + queries['entry_title'] + '&search_location=' + queries['entry_location'] + '\'')
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
    queries = addDefaults(queries, {'category_category': '', 'category_amount': '', 'category_title': '', 'category_location': '', 'category_account': ''})

    try:
        name = addCategory(finances, queries['category_category'], queries['category_amount'], queries['category_title'], queries['category_location'], queries['category_account'])

        # redirect to a history page of the category
        redirect = meta(content='0; URL=\'/history?search_category=' + name + '\'')
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
        menuCell.add( a('About', href='/about', cls='option') )
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
        elif path.startswith('/editentry'):
            body = WEBeditEntry(finances, queries)
        elif path.startswith('/rename'):
            body = WEBrenameAccount(finances, queries)
        elif path.startswith('/delete'):
            body = WEBdelete(finances, queries)
        elif path.startswith('/about'):
            pageName = 'About'
            body = WEBabout(finances, queries)
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