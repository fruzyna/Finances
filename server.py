import http.server, re, urllib.parse

from control import *

HOST = '127.0.0.1'
PORT = 8080

class requestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # generate the web page
        text = self.generate_page()
        self.wfile.write(bytes(text, 'utf8'))
        return

    # generate web page based off url and queries
    def generate_page(self):
        # load in finance data
        confDir, accounts, categories, log = load()

        # load in base page from file
        body = 'No page.'
        with open('base.html', 'r') as f:
            body = f.read()

        text = ''
        # remove encoding from url
        path = urllib.parse.unquote_plus(self.path)
        if path.startswith('/history'):
            # history tab
            # read queries and create defaults
            queries = {'results': '5', 'title': '', 'loc': '', 'acct': '', 'amount': '', 'note': '', 'cat': '', 'start': '', 'end': '', 'transType': ''}
            queryStrs = re.findall('([A-z0-9]+=[^&]+)', path)
            for q in queryStrs:
                key, val = q.split('=')
                if key[-1] == '?':
                    key = key[:-1]
                queries[key] = val
            
            # load in base history section
            text = 'No page.'
            with open('innerHTML/history.html', 'r') as f:
                text = f.read()

            # fill in blanks with text from queries
            text = text.replace('{:RESULTS:}', queries['results'])
            text = text.replace('{:TITLE:}', correctFormat('title', queries['title']))
            text = text.replace('{:LOC:}', correctFormat('location', queries['loc']))
            text = text.replace('{:START:}', correctFormat('date', queries['start']))
            text = text.replace('{:END:}', correctFormat('date', queries['end']))

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
            for acct in [''] + accounts:
                selected = ''
                if acct == queries['acct']:
                    selected = ' selected="selected"'
                accts += '<option value="' + acct + '"' + selected + '>' + acct + '</option>'
            text = text.replace('{:ACCTS:}', accts)

            # fill in categories
            cats = ''
            keys = [''] + [key for key in categories] 
            for cat in keys:
                selected = ''
                if cat == queries['cat']:
                    selected = ' selected="selected"'
                cats += '<option value="' + cat + '"' + selected + '>' + cat + '</option>'
            text = text.replace('{:CATS:}', cats)

            # search database
            results = getLast(log, int(queries['results']), categories, title=queries['title'], location=queries['loc'], acct=queries['acct'], start=queries['start'], end=queries['end'], transType=queries['transType'], category=queries['cat'])
            
            # place column names in table
            cols = ''
            for col in results.columns:
                cols += '<td>' + col + '</td>'
            text = text.replace('{:HEADERS:}', cols)
            
            # build each row of results in table
            rows = ''
            for _, row in results.iterrows():
                rows += '<tr>'
                for value in row:
                    rows += '<td>' + str(value) + '</td>'
                rows += '</tr>'
            text = text.replace('{:ROWS:}', rows)
        elif path.startswith('/addlog'):
            # request to create a new log entry
            # read queries and create defaults
            queries = {'title': '', 'loc': '', 'date': '', 'to': '', 'from': '', 'amount': '', 'note': ''}
            queryStrs = re.findall('([A-z0-9]+=[^&]+)', path)
            for q in queryStrs:
                key, val = q.split('=')
                if key[-1] == '?':
                    key = key[:-1]
                queries[key] = val

            # create the row and save to file
            log.loc[log.shape[0]] = [correctFormat('title', queries['title']), correctFormat('location', queries['loc']), correctFormat('date', queries['date']), queries['from'], queries['to'], correctFormat('amount', queries['amount']), correctFormat('note', queries['note'])]
            logFile = confDir + 'log.csv'
            save(log, logFile)

            # redirect to a history page showing the last entry (may not be the new one)
            text = '<meta http-equiv="refresh" content="0; URL=\'/history?results=1\'" />'
        elif path.startswith('/addacct'):
            # request to create a new account
            # read queries and create defaults
            queries = {'name': ''}
            queryStrs = re.findall('([A-z0-9]+=[^&]+)', path)
            for q in queryStrs:
                key, val = q.split('=')
                if key[-1] == '?':
                    key = key[:-1]
                queries[key] = val
            newAcct = correctFormat('account', queries['name'], new=True)

            # add the account to the accounts file
            accounts.append(newAcct)
            acctFile = confDir + 'accounts.csv'
            with open(acctFile, 'w+') as f:
                f.write(','.join(accounts))

            # redirect to the balances page
            text = '<meta http-equiv="refresh" content="0; URL=\'/balance\'" />'
        elif path.startswith('/addcat'):
            # request to create a new category
            # read queries and create defaults
            queries = {'name': '', 'goal': '', 'titles': '', 'locs': '', 'accts': ''}
            queryStrs = re.findall('([A-z0-9]+=[^&]+)', path)
            for q in queryStrs:
                key, val = q.split('=')
                if key[-1] == '?':
                    key = key[:-1]
                queries[key] = val

            # process queries
            name    = correctFormat('category', queries['name'], new=True)
            goal    = correctFormat('amount', queries['goal'])
            titles  = [correctFormat('title', title) for title in queries['titles'].split(',')]
            locs    = [correctFormat('location', loc) for loc in queries['locs'].split(',')]
            accts   = [correctFormat('account', acct, accounts=accounts) for acct in queries['accts'].split(',')]

            # add the categories to the categories file
            categories[name] = [goal, titles, locs, accts]
            catFile = confDir + 'categories.csv'
            with open(catFile, 'w+') as f:
                for catName in categories:
                    cat = categories[catName]
                    goal    = cat[0]
                    titles  = cat[1]
                    locs    = cat[2]
                    accts   = cat[3]
                    f.write(catName + ',' + str(goal) + ',' + ':'.join(titles) + ',' + ':'.join(locs) + ',' + ':'.join(accts) + '\n')

            # redirect to a history page of the category
            text = '<meta http-equiv="refresh" content="0; URL=\'/history?cat=' + name + '\'" />'
        elif path.startswith('/add'):
            # add tab
            # load in base add section
            text = 'No page.'
            with open('innerHTML/add.html', 'r') as f:
                text = f.read()

            # fill in accounts
            accts = ''
            for acct in [''] + accounts:
                accts += '<option value="' + acct + '">' + acct + '</option>'
            text = text.replace('{:ACCTS:}', accts)
        else:
            # balances tab
            # load in base balances section
            text = 'No page.'
            with open('innerHTML/balance.html', 'r') as f:
                text = f.read()
                
            # get each accounts balance and process
            accts = ''
            total = 0
            for acct in accounts:
                _,_, delta, _,_,_ = getAccountInfo(log, acct)
                valStr = valueToString(delta)
                accts += '<tr><td>' + acct + '</td><td>' + str(valStr) + '</td></tr>'
                total += delta
            # add total
            accts += '<tr><td>Total</td><td>' + valueToString(total) + '</td></tr>'
            # fill in all accounts
            text = text.replace('{:ACCTS:}', accts)
        # add the requested section to the core of the webpage
        body = body.replace('{:BODY:}', str(text))
        return body

# start server
with http.server.HTTPServer((HOST, PORT), requestHandler) as httpd:
    print('Running server on', PORT)
    httpd.serve_forever()