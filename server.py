import http.server, re

from control import *

HOST = '127.0.0.1'
PORT = 8080

confDir, accounts, categories, log = load()

class requestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)

        self.send_header('Content-type', 'text/html')
        self.end_headers()

        text = self.generate_page()
        self.wfile.write(bytes(text, 'utf8'))
        return

    def generate_page(self):
        body = 'No page.'
        with open('base.html', 'r') as f:
            body = f.read()

        text = ''
        if self.path.startswith('/balance'):
            # get each accounts balance and process
            total = 0
            text = '<table><tr class="header"><td>Account</td><td>Balance</td></tr>'
            for acct in accounts:
                _,_, delta, _,_,_ = getAccountInfo(log, acct)
                valStr = valueToString(delta)
                text += '<tr><td>' + acct + '</td><td>' + str(valStr) + '</td></tr>'
                total += delta
            text += '<tr><td>Total</td><td>' + valueToString(total) + '</td></tr></table>'
        elif self.path.startswith('/history'):
            text = '<table><tr class="header">'
            queries = {'results': '5', 'title': '', 'loc': '', 'date': '', 'acct': '', 'amount': '', 'note': '', 'cat': '', 'start': '', 'end': '', 'transType': ''}
            queryStrs = re.findall('([A-z0-9]+=[^&]+)', self.path)
            for q in queryStrs:
                key, val = q.split('=')
                if key[-1] == '?':
                    key = key[:-1]
                queries[key] = val
            results = getLast(log, int(queries['results']), categories, title=queries['title'], location=queries['loc'], acct=queries['acct'], start=queries['start'], end=queries['end'], transType=queries['transType'], category=queries['cat'])
            for col in results.columns:
                text += '<td>' + col + '</td>'
            text += '</tr>'
            for _, row in results.iterrows():
                text += '<tr>'
                for value in row:
                    text += '<td>' + str(value) + '</td>'
                text += '</tr>'
            text += '</table>'
        body = body.replace('{:BODY:}', str(text))
        return body

with http.server.HTTPServer((HOST, PORT), requestHandler) as httpd:
    print('Running server on', PORT)
    httpd.serve_forever()