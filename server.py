import http.server, re, urllib.parse, ssl
import matplotlib.pyplot as plt

from control import *
from features import *

HOST = ''
PORT = 8080

def addDefaults(queries, defaults):
    for key in defaults:
        if not key in queries:
            queries[key] = defaults[key]
    return queries

def WEBhistory(finances, queries, path):
    # history tab
    # read queries and create defaults
    queries = addDefaults(queries, {'results': '5', 'title': '', 'loc': '', 'acct': '', 'amount': '', 'note': '', 'cat': '', 'start': '', 'end': '', 'transType': '', 'plot': '', 'edit': ''})
    
    # load in base history section
    text = 'No page.'
    with open('innerHTML/history.html', 'r') as f:
        text = f.read()

    # fill in blanks with text from queries
    text = text.replace('{:RESULTS:}', queries['results'])
    text = text.replace('{:TITLE:}', correctFormat(finances, 'title', queries['title']))
    text = text.replace('{:LOC:}', correctFormat(finances, 'location', queries['loc']))
    text = text.replace('{:START:}', correctFormat(finances, 'date', queries['start']))
    text = text.replace('{:END:}', correctFormat(finances, 'date', queries['end']))

    # fill in transaction type options
    trans = ''
    for tt in ['', 'to', 'from', 'transfer']:
        selected = ''
        if tt == queries['transType']:
            selected = ' selected="selected"'
        trans += '<option value="' + tt + '"' + selected + '>' + tt + '</option>'
    text = text.replace('{:TRANSTYPE:}', trans)

    # fill in accounts
    accts = ''
    for acct in [''] + finances.accounts:
        selected = ''
        if acct == queries['acct']:
            selected = ' selected="selected"'
        accts += '<option value="' + acct + '"' + selected + '>' + acct + '</option>'
    text = text.replace('{:ACCTS:}', accts)

    # fill in categories
    cats = ''
    keys = [''] + [key for key in finances.categories] 
    for cat in keys:
        selected = ''
        if cat == queries['cat']:
            selected = ' selected="selected"'
        cats += '<option value="' + cat + '"' + selected + '>' + cat + '</option>'
    text = text.replace('{:CATS:}', cats)

    # search database
    results, total = showHistory(finances, queries['results'], queries['acct'], queries['start'], queries['end'], queries['title'], queries['loc'], queries['note'], queries['cat'], queries['transType'])
    
    # place column names in table
    cols = '<td>row</td>'
    for col in results.columns:
        cols += '<td>' + col + '</td>'
    cols += '<td>edit</td>'
    text = text.replace('{:HEADERS:}', cols)
    
    # build each row of results in table
    rows = ''
    for i, row in results.iterrows():
        i = str(i)
        rows += '<tr>'
        if i == queries['edit']:
            rows += '<form id="edit" action="/edit">'
            rows += '<td><input type="text" name="row" value="' + i + '" size="3" readonly></td>'
            rows += '<td><input type="text" name="title" value="' + str(row['title']) + '"></td>'
            rows += '<td><input type="text" name="location" value="' + str(row['location']) + '"></td>'
            rows += '<td><input type="text" name="date" value="' + str(row['date']).split(' ')[0] + '"></td>'
            rows += '<td><select name="from" form="edit">'
            for acct in [''] + finances.accounts:
                selected = ''
                if acct == str(row['from']):
                    selected = ' selected="selected"'
                rows += '<option value="' + acct + '"' + selected + '>' + acct + '</option>'
            rows += '</select></td>'
            rows += '<td><select name="to" form="edit">'
            for acct in [''] + finances.accounts:
                selected = ''
                if acct == str(row['to']):
                    selected = ' selected="selected"'
                rows += '<option value="' + acct + '"' + selected + '>' + acct + '</option>'
            rows += '</select></td>'
            rows += '<td><input type="number" name="amount" value="' + str(row['amount']) + '" min="0" step=".01"></td>'
            rows += '<td><input type="text" name="note" value="' + str(row['note']) + '"></td>'
            rows += '<td><input type="submit" value="Submit"></td>'
            rows += '</form>'
        else:
            rows += '<td>' + i + '</td>'
            for value in row:
                rows += '<td>' + str(value) + '</td>'
            rows += '<td><a href="' + path + '&edit=' + i + '">edit</a> <a href="/delete?row=' + i + '">delete</a></td>'
        rows += '</tr>'
    text = text.replace('{:ROWS:}', rows)

    if queries['plot'] == 'on':
        visualHistory(finances, results)
        plt.savefig('vhist.png')
        text += '<img src="vhist.png">'
        text = text.replace('{:CHECKED:}', ' checked')
    text = text.replace('{:CHECKED:}', '')
    return text

def WEBedit(finances, queries):
    queries = addDefaults(queries, {'title': '', 'location': '', 'date': dt.today().strftime(dateFormat), 'to': '', 'from': '', 'amount': '', 'note': '', 'row': ''})
    editWhole(finances, queries['row'], queries['title'], queries['location'], queries['date'], queries['from'], queries['to'], queries['amount'], queries['note'])
    text = '<meta http-equiv="refresh" content="0; URL=\'/history\'" />'
    return text

def WEBdelete(finances, queries):
    queries = addDefaults(queries, {'row': ''})
    delete(finances, queries['row'], 'y')
    text = '<meta http-equiv="refresh" content="0; URL=\'/history\'" />'
    return text

def WEBadd(finances, queries):
    # request to create a new log entry
    # read queries and create defaults
    queries = addDefaults(queries, {'title': '', 'loc': '', 'date': dt.today().strftime(dateFormat), 'to': '', 'from': '', 'amount': '', 'note': ''})

    # create the row and save to file
    success = add(finances, queries['title'], queries['loc'], queries['date'], queries['from'], queries['to'], queries['amount'], queries['note'])

    # redirect to a history page showing the last entry (may not be the new one)
    text = '<meta http-equiv="refresh" content="0; URL=\'/history?results=1\'" />'
    return text

def WEBaddAccount(finances, queries):
    # request to create a new account
    # read queries and create defaults
    queries = addDefaults(queries, {'name': ''})

    addAccount(finances, queries['name'])
        
    # redirect to the balances page
    text = '<meta http-equiv="refresh" content="0; URL=\'/balance\'" />'
    return text

def WEBaddCategory(finances, queries):
    # request to create a new category
    # read queries and create defaults
    queries = addDefaults(queries, {'name': '', 'goal': '', 'titles': '', 'locs': '', 'accts': ''})

    name = addCategory(finances, queries['name'], queries['goal'], queries['titles'], queries['locs'], queries['accts'])

    # redirect to a history page of the category
    text = '<meta http-equiv="refresh" content="0; URL=\'/history?cat=' + name + '\'" />'
    return text

def WEBaddPage(finances, queries):
    # add tab
    # load in base add section
    text = 'No page.'
    with open('innerHTML/add.html', 'r') as f:
        text = f.read()

    # fill in accounts
    accts = ''
    for acct in [''] + finances.accounts:
        accts += '<option value="' + acct + '">' + acct + '</option>'
    text = text.replace('{:ACCTS:}', accts)
    return text

def WEBplot(finances, queries):
    # plot tab
    # read queries and create defaults
    queries = addDefaults(queries, {'units': 'days', 'acct': '', 'start': '', 'end': '', 'invert': '', 'points': '', 'noLine': '', 'allPoints': '', 'totals': ''})
    
    # load in base history section
    text = 'No page.'
    with open('innerHTML/plot.html', 'r') as f:
        text = f.read()

    # fill in blanks with text from queries
    text = text.replace('{:START:}', correctFormat(finances, 'date', queries['start']))
    text = text.replace('{:END:}', correctFormat(finances, 'date', queries['end']))

    invert = queries['invert'] == 'on'
    if invert:
        text = text.replace('{:ICHECKED:}', ' checked')
    else:
        text = text.replace('{:ICHECKED:}', '')

    points = queries['points'] == 'on'
    if points:
        text = text.replace('{:PCHECKED:}', ' checked')
    else:
        text = text.replace('{:PCHECKED:}', '')

    noLine = queries['noLine'] == 'on'
    if noLine:
        text = text.replace('{:NCHECKED:}', ' checked')
    else:
        text = text.replace('{:NCHECKED:}', '')

    allPoints = queries['allPoints'] == 'on'
    if allPoints:
        text = text.replace('{:ACHECKED:}', ' checked')
    else:
        text = text.replace('{:ACHECKED:}', '')

    totals = queries['totals'] == 'on'
    if totals:
        text = text.replace('{:TCHECKED:}', ' checked')
    else:
        text = text.replace('{:TCHECKED:}', '')

    # fill in transaction type options
    trans = ''
    for tt in ['days', 'weeks', 'months', 'quarters', 'years']:
        selected = ''
        if tt == queries['units']:
            selected = ' selected="selected"'
        trans += '<option value="' + tt + '"' + selected + '>' + tt + '</option>'
    text = text.replace('{:UNITS:}', trans)

    # fill in accounts
    accts = ''
    for acct in [''] + finances.accounts:
        selected = ''
        if acct == queries['acct']:
            selected = ' selected="selected"'
        accts += '<option value="' + acct + '"' + selected + '>' + acct + '</option>'
    text = text.replace('{:ACCTS:}', accts)

    # search database
    plot(finances, queries['units'], queries['acct'], queries['start'], queries['end'], invert, points, noLine, allPoints, totals)
    plt.savefig('plot.png')
    text += '<img src="plot.png">'
    return text

def WEBgoalProgress(finances, queries):
    # goals tab
    # load in base balances section
    text = 'No page.'
    with open('innerHTML/goals.html', 'r') as f:
        text = f.read()
        
    # get each accounts balance and process
    cats = ''
    for cat in finances.categories:
        first, last, month, igoal, spent, sgoal, progress = goalProgress(finances, cat, '', '')
        if igoal > 0:
            cats += '<tr><td>' + cat + '</td><td>' + sgoal + '</td><td>' + spent + '</td><td>' + progress + '%</td></tr>'
        else:
            cats += '<tr><td>' + cat + '</td><td>No Goal</td><td>' + spent + '</td><td></td></tr>'
    # fill in all accounts
    text = text.replace('{:CATS:}', cats)
    text += '(from ' + first + ' to ' + last + ')'
    return text

def WEBbalance(finances, queries):
    # balances tab
    # load in base balances section
    text = 'No page.'
    with open('innerHTML/balance.html', 'r') as f:
        text = f.read()
        
    # get each accounts balance and process
    accts = ''
    total = 0
    balances = balance(finances)
    for acct in balances:
        accts += '<tr><td>' + acct + '</td><td>' + balances[acct] + '</td></tr>'
    # fill in all accounts
    text = text.replace('{:ACCTS:}', accts)
    return text

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
        finances = load()

        # load in base page from file
        body = 'No page.'
        with open('base.html', 'r') as f:
            body = f.read()

        text = ''
        # remove encoding from url
        path = urllib.parse.unquote_plus(self.path)
        page = ''
        queries = {}
        queryStrs = re.findall('([A-z0-9]+=[^&]+)', path)
        for q in queryStrs:
            key, val = q.split('=')
            if key[-1] == '?':
                key = key[:-1]
            queries[key] = val
        page = ''
        if path.startswith('/history'):
            page = 'History'
            text = WEBhistory(finances, queries, path)
        elif path.startswith('/addlog'):
            text = WEBadd(finances, queries)
        elif path.startswith('/addacct'):
            text = WEBaddAccount(finances, queries)
        elif path.startswith('/addcat'):
            text = WEBaddCategory(finances, queries)
        elif path.startswith('/add'):
            page = 'Add'
            text = WEBaddPage(finances, queries)
        elif path.startswith('/plot'):
            page = 'Plot'
            text = WEBplot(finances, queries)
        elif path.startswith('/goals'):
            page = 'Goals'
            text = WEBgoalProgress(finances, queries)
        elif path.startswith('/edit'):
            text = WEBedit(finances, queries)
        elif path.startswith('/delete'):
            text = WEBdelete(finances, queries)
        else:
            page = 'Balances'
            text = WEBbalance(finances, queries)
        # add the requested section to the core of the webpage
        body = body.replace('{:PAGE:}', page)
        body = body.replace('{:BODY:}', str(text))
        return body

# start server
with http.server.HTTPServer((HOST, PORT), requestHandler) as httpd:
    #httpd.socket = ssl.wrap_socket(httpd.socket, keyfile='key.pem', certfile='cert.pem', server_side=True)
    print('Running server at http://localhost:' + str(PORT))
    httpd.serve_forever()