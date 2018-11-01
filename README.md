# Finances
Python script for basic tracking of my finances

Commands
Optional arguments use --
Dates are in MM/DD/YYYY format, I agree it sucks, but it's habit
- add
  - Add a new transaction to the log
  - add [title]@[location] [account] [delta] --date [date]
- listAccts
  - Lists all registered accounts
  - listAccts
- help
  - Displays help dialog
  - help
- link
  - Links the config directory to a given location, useful for storing data in Dropbox
  - link [new config dir]
- plot
  - Plots a given account to a graph
  - plot [days/months] --acct [account] --start [start date] --end [end date]
- acctInfo
  - Displays some summary stats about an account
  - acctInfo [account] --start [start date] --end [end date]
- hist
  - Displays the last x items, default is 5
  - hist [items] --acct [account] --start [start date] --end [end date] --loc [location] --title [title] --transType [to/from/transfer] --note [note]
- balance
  - Displays the balance of all accounts and total
  - balance
- newAcct
  - Register a new account
  - newAcct [name]
- export
  - Export log to a new file in the current directory
  - export [name]
