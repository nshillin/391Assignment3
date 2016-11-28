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
            continue
        if new_triple[i][0] == '<' and new_triple[i][-1] == '>':
            temp = new_triple[i]
            if '#' in temp:
                pos = temp.rfind('#')
            elif temp.count('/') > 2:
                pos = temp.rfind('/')
            else:
                new_triple[i] = temp.replace('<','').replace('>','')
                continue
            prefixes[temp[1:pos+1]] = temp[:pos+1]+'>'
            new_triple[i] = temp[1:-1]
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
    error("Expected 'python q8.py <db file> <RDF Turtle file>'")


prefixes = {}
triples = []
prev_triple = []
expected = 3

conn = sqlite3.connect(args[1])
conn.text_factory = str
c = conn.cursor()

for line in open(args[2]):
    if line.startswith("@prefix"):
        if not prefix(line): error("Line not formatted properly: " + line)
    else:
        splitLine(line.strip('\n')[0:-2] + '\t' + line.strip('\n')[-1])



#try_query("CREATE TABLE prefix (uri text, unique (uri))")
try_query("CREATE TABLE IF NOT EXISTS rdfStore (subj text, pred text, obj text, unique (subj, pred, obj))")

for triple in triples:
    for i in range(len(triple)):
        position = triple[i].find(':')
        if position != -1:
            prefix = triple[i][:position+1]
            if (prefix in prefixes) and triple[i].startswith(prefix):
                triple[i] = triple[i].replace(prefix,prefixes[prefix])
        triple[i] = triple[i].replace('<','').replace('>','')
    try_query("INSERT INTO rdfStore (subj, pred, obj) VALUES (?,?,?)",(triple[0], triple[1], triple[2]))

try_query("CREATE INDEX IF NOT EXISTS rdfIndex ON rdfStore (subj, pred, obj)")

conn.commit()
conn.close()

#https://docs.python.org/2/library/sqlite3.html


# Create prefix table and fill it with contents that it doesn't already have


#EXAMPLE: c.execute('''CREATE TABLE prefix (start text, uri text, symbol text, qty real, price real)''')
