import http.server, re

from control import *

HOST = '127.0.0.1'
PORT = 8080

class requestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        text = self.generate_page()
        self.wfile.write(bytes(text, 'utf8'))
        return

    def generate_page(self):
        confDir, accounts, categories, log = load()

        body = 'No page.'
        with open('base.html', 'r') as f:
            body = f.read()

        text = ''
        if self.path.startswith('/history'):
            queries = {'results': '5', 'title': '', 'loc': '', 'acct': '', 'amount': '', 'note': '', 'cat': '', 'start': '', 'end': '', 'transType': ''}
            queryStrs = re.findall('([A-z0-9]+=[^&]+)', self.path)
            for q in queryStrs:
                key, val = q.split('=')
                if key[-1] == '?':
                    key = key[:-1]
                queries[key] = val.replace('+', ' ')
            text += '<form id="hist"><table>'
            text += '<tr><td>Results: '
            text += '<input type="number" name="results" size="4" value="' + queries['results'] + '"></td>'
            text += '<td>Title: '
            text += '<input type="text" name="title" value="' + queries['title'] + '"></td>'
            text += '<td>Location: '
            text += '<input type="text" name="loc" value="' + queries['loc'] + '"></td></tr>'
            text += '<tr><td>Transfer Type: '
            text += '<select name="transType" form="hist">'
            for tt in ['', 'to', 'from', 'transfer']:
                selected = ''
                if tt == queries['transType']:
                    selected = ' selected="selected"'
                text += '<option value="' + tt + '"' + selected + '>' + tt + '</option>'
            text += '</select></td>'
            text += '<td>Account: '
            text += '<select name="acct" form="hist">'
            for acct in [''] + accounts:
                selected = ''
                if acct == queries['acct']:
                    selected = ' selected="selected"'
                text += '<option value="' + acct + '"' + selected + '>' + acct + '</option>'
            text += '</select></td>'
            text += '<td>Category: '
            text += '<select name="cat" form="hist">'
            keys = [''] + [key for key in categories] 
            for cat in keys:
                selected = ''
                if cat == queries['cat']:
                    selected = ' selected="selected"'
                text += '<option value="' + cat + '"' + selected + '>' + cat + '</option>'
            text += '</select></td></tr>'
            text += '<tr><td>Start Date: '
            text += '<input type="text" name="start" size="10" value="' + queries['start'] + '"></td>'
            text += '<td>End Date: '
            text += '<input type="text" name="end" size="10" value="' + queries['end'] + '"></td>'
            text += '<td><input type="submit" value="Search"></td></tr>'
            text += '</table></form>'
            results = getLast(log, int(queries['results']), categories, title=queries['title'], location=queries['loc'], acct=queries['acct'], start=queries['start'], end=queries['end'], transType=queries['transType'], category=queries['cat'])
            text += '<table class="data"><tr class="header">'
            for col in results.columns:
                text += '<td>' + col + '</td>'
            text += '</tr>'
            for _, row in results.iterrows():
                text += '<tr>'
                for value in row:
                    text += '<td>' + str(value) + '</td>'
                text += '</tr>'
            text += '</table>'
        elif self.path.startswith('/log'):
            queries = {'title': '', 'loc': '', 'date': '', 'to': '', 'from': '', 'amount': '', 'note': ''}
            queryStrs = re.findall('([A-z0-9]+=[^&]+)', self.path)
            for q in queryStrs:
                key, val = q.split('=')
                if key[-1] == '?':
                    key = key[:-1]
                queries[key] = val.replace('+', ' ')

            log.loc[log.shape[0]] = [correctFormat('title', queries['title']), correctFormat('location', queries['loc']), correctFormat('date', queries['date']), queries['from'], queries['to'], correctFormat('amount', queries['amount']), correctFormat('note', queries['note'])]
            logFile = confDir + 'log.csv'
            save(log, logFile)

            text = '<meta http-equiv="refresh" content="0; URL=\'/history\'" />'
        elif self.path.startswith('/add'):
            text += '<form id="add" action="/log"><table>'
            text += '<tr><td>Title: '
            text += '<input type="text" name="title"></td>'
            text += '<td>Location: '
            text += '<input type="text" name="loc"></td></tr>'
            text += '<tr><td>From: '
            text += '<select name="from" form="add">'
            for acct in [''] + accounts:
                text += '<option value="' + acct + '">' + acct + '</option>'
            text += '</select></td>'
            text += '<td>To: '
            text += '<select name="to" form="add">'
            for acct in [''] + accounts:
                text += '<option value="' + acct + '">' + acct + '</option>'
            text += '</select></td>'
            text += '<td>Amount: '
            text += '<input type="number" name="amount"></td></tr>'
            text += '<tr><td>Date: '
            text += '<input type="text" name="date" size="10"></td>'
            text += '<td>Note: '
            text += '<input type="text" name="note" size="10"></td>'
            text += '<td><input type="submit" value="Log"></td>'
            text += '</table></form>'
        else:
            # get each accounts balance and process
            total = 0
            text = '<table class="data"><tr class="header"><td>Account</td><td>Balance</td></tr>'
            for acct in accounts:
                _,_, delta, _,_,_ = getAccountInfo(log, acct)
                valStr = valueToString(delta)
                text += '<tr><td>' + acct + '</td><td>' + str(valStr) + '</td></tr>'
                total += delta
            text += '<tr><td>Total</td><td>' + valueToString(total) + '</td></tr></table>'
        body = body.replace('{:BODY:}', str(text))
        return body

with http.server.HTTPServer((HOST, PORT), requestHandler) as httpd:
    print('Running server on', PORT)
    httpd.serve_forever()