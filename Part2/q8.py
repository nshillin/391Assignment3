import sqlite3
import sys

def prefix(line):
    # Prefix format: "rdf":"<http://www.w3.org/1999/02/22-rdf-syntax-ns#>"
    global prefixes
    l = line.split()
    if len(l) == 4 and l[-1] == '.':
        prefixes[l[1]] = l[2]
        return True
    return False

def splitLine(line):
    global triples, expected, prev_triple
    l = line.replace('\t\t','\t').split('\t')
    new_triple = []
    if line.startswith("\t\t") and expected == 1 and len(l) == 3: new_triple = [prev_triple[0],prev_triple[1],l[-2]]
    elif line.startswith("\t") and expected == 2 and len(l) == 4: new_triple = [prev_triple[0],l[-3],l[-2]]
    elif expected == 3 and len(l) == 4: new_triple = [l[0],l[1],l[2]]
    else: error("Error: " + line)
    should_append = True
    for i in range(len(new_triple)):
        if ('@' in new_triple[i] and '@en' in new_triple[i]) or '@' not in new_triple[i]:
            new_triple[i] = new_triple[i].split('^^')[0].replace('@en','').strip('"')
        else:
            should_append = False
    if should_append:
        triples.append(new_triple)
        prev_triple = new_triple
    if l[-1] == ',': expected = 1
    elif l[-1] == ';': expected = 2
    elif l[-1] == '.': expected = 3
    else: error("Error: unexpected identifier at end of line: " + line)

def error(errorType):
    print errorType
    sys.exit()

def try_query(query,extras = ()):
    global c
    try: c.execute(query,extras)
    except Exception,error:
        if "UNIQUE" not in str(error) and "exists" not in str(error):
            print str(error)

##### START OF MAIN CODE #####

args  = sys.argv
if len(args) != 3:
    error("Expected 'python q8.py <db file> <RDF Turtle file>")


prefixes = {'other':'NULL'}
triples = []
prev_triple = []
expected = 3

for line in open(args[2]):
    if line.startswith("@prefix"):
        if not prefix(line): error("Line not formatted properly: " + line)
    else:
        splitLine(line.strip('\n')[0:-2] + '\t' + line.strip('\n')[-1])


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
