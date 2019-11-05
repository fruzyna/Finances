from dominate.tags import *

def addDefaults(queries, defaults):
    for key in defaults:
        if not key in queries:
            queries[key] = defaults[key]
    return queries

def newQuery(queries):
    query_str = ''
    for item in queries.items():
        key, value = item
        query_str += '&' + key + '=' + str(value)
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