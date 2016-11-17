import sqlite3
import sys
import re

def prefix(line):
    global prefixes
    l = line.split()
    if len(l) == 3:
        prefixes[l[1]] = l[2]
        return True
    return False

def error(errorType):
    print errorType
    sys.exit()


##### START OF MAIN CODE #####

args  = sys.argv
if len(args) != 3:
    error("Expected 'python q8.py <db file> <query file>'")


prefixes = {'other':'NULL'}
variables = []
prev_triple = []
expected = 3

for line in open(args[2]):
    line = line.lower()
    if line.startswith("prefix"):
        if not prefix(line): error("Line not formatted properly: " + line)
    elif line.startswith("select"):
        splitLine(line.strip('\n')[0:-2] + '\t' + line.strip('\n')[-1])
    elif line.startswith("where"):
        pass
    elif line.startswith("}"):
        pass
    else:


conn = sqlite3.connect(args[1])
c = conn.cursor()

try_query("CREATE TABLE prefix (prefixid INTEGER PRIMARY KEY,start text, url text, unique (start))")

for i in prefixes:
    try_query("INSERT INTO prefix (start,url) VALUES (?,?)",(i,prefixes[i]))

try_query('CREATE TABLE tripletables (tableid INTEGER PRIMARY KEY, tablename text, unique (tablename))')

triple_styles = []
for triple in triples:
    new_triple_style = []
    for i in range(len(triple)):
        for t in prefixes:
            if triple[i].startswith(t):
                new_triple_style.append(t)
                break
        if len(new_triple_style) != i+1:
            new_triple_style.append("other")
    table_name = '"' + new_triple_style[0] + new_triple_style[1] + new_triple_style[2] + '"'
    if new_triple_style not in triple_styles:
        triple_styles.append(new_triple_style)
        # Try to create new table
        try_query('CREATE TABLE ' + table_name + ' (subj text, pred text, obj text, unique (subj,pred,obj))')
        try_query("INSERT INTO tripletables (tablename) VALUES (?)",(table_name,))
    # Insert values
    try_query("INSERT INTO " + table_name + ' VALUES ("'+triple[0]+'","'+triple[1]+'","'+triple[2]+'")')


conn.commit()
conn.close()

#https://docs.python.org/2/library/sqlite3.html


# Create prefix table and fill it with contents that it doesn't already have


#EXAMPLE: c.execute('''CREATE TABLE prefix (start text, url text, symbol text, qty real, price real)''')
