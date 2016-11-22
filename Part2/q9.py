import sqlite3
import sys
import re

types = ["subj","pred","obj"]

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

def try_query(query,extras = ()):
    global c
    try: c.execute(query,extras)
    except Exception,error:
        if "UNIQUE" not in str(error) and "exists" not in str(error):
            print str(error)

def checkPrefixes():
    global c
    for i in prefixes:
        try_query('SELECT url FROM prefix WHERE start=?',(i,))
        url = c.fetchone()[0]
        if url == None:
            print "Invalid prefix: " + i
            print "Attempting to complete without..."
        elif url != prefixes[i]:
            print "Invalid url: " + prefixes[i]
            error("try " + url + " instead")

def getTableNames():
    tablenames = []
    symbols = []
    for x in triple_styles[i]:
        if x == '': symbols.append('>')
        else: symbols.append('=')
    for tablename in c.execute('SELECT tablename FROM tripletables where subj'+symbols[0]+'? and pred'+symbols[1]+'? and obj'+symbols[2]+'?',tuple(triple_styles[i])):
        tablenames.append(str(tablename[0]))
    return tablenames

#OLD
#def makeSelect(triple):
#    select = "SELECT "
#    for y in range(len(triple)):
#        if triple[y] in allVariables:
#            select += types[y]+", "
#    return select[:-2]

def makeWhere(triple):
    #'where subj'+symbols[0]+'? and pred'+symbols[1]+'? and obj'+symbols[2]+'?',tuple(temp_triple)
    global allVariables
    where = " WHERE "
    for y in range(len(triple)):
        if triple[y] not in allVariables:
            where += types[y]+'="'+triple[y]+'" and '
        elif len(allVariables[triple[y]])>0:
            where += '('
            for value in allVariables[triple[y]]:
                where += types[y]+'="'+value+'" or '
            where = where[:-4] + ') and '
    for e in triple:
        if e in allVariables:
            allVariables[e] = []
    return where[:-4]

def printTable(variables,printVariables):
    if printVariables[0] == '*':
        for e in allVariables:
            printVariables.append(e)
    sep = '|| '
    printList = [sep]*(len(variables[max(variables, key= lambda y: len(set(variables[y])))])+2)
    for a in printVariables:
        width = len(a)+1
        if len(variables[a])>0:width = len(max(variables[a], key=len))+1
        printList[0] += a+" "*(width-len(a))+sep
        printList[1] += "="*(width-1)+" "+sep
        for e in range(len(printList)-2):
            if e<len(variables[a]):
                var = variables[a][e]
                printList[e+2] += var+(" "*(width-len(var)))+sep
            else:
                printList[e+2] += " "*(width)+sep
    for x in printList:
        print x


##### START OF MAIN CODE #####

args  = sys.argv
if len(args) != 3:
    error("Expected 'python q8.py <db file> <query file>'")

prefixes = {'other':'NULL'}
printVariables = []
allVariables = {} # variable object example: "?city:['dbr:Edmonton','dbr:Calgary']"
triples = []

with open(args[2], 'r') as queryFile:
    text=queryFile.read()


for e in re.findall(r"prefix\s+(.+:)\s*(<[^\s]+>)",text,re.I):
    prefixes[e[0]] = e[1]

printVariables = re.search(r"select\s+(.+)where\s+{",text,re.I).group(1).split()
for e in printVariables:
    if e!='*': allVariables[e] = []
temp_list = querySearch = re.search(r"where\s+\{\s*([^\}]+)\}",text,re.I).group(1).split('\n')
print temp_list
#filter\s*regex\((.*),\s*(.*)\)
triples = [[]]
triple_styles = [[]]
# [('Filter',position)]
order = []

for i in range(len(temp_list)):
    if temp_list[i] != '.':
        triples[-1].append(temp_list[i])
        if temp_list[i].startswith('?'):
            allVariables[temp_list[i]] = []
            triple_styles[-1].append("")
        else:
            found = False
            for t in prefixes:
                if temp_list[i].startswith(t):
                    triple_styles[-1].append(t)
                    found = True
                    break
            if not found:
                triple_styles[-1].append("other")
    elif i<len(temp_list)-1:
        triples.append([])
        triple_styles.append([])

"""
OLD
for i in range(len(temp_list)):
    if temp_list[i] != '.':
        triples[-1].append(temp_list[i])
        if temp_list[i].startswith('?'):
            allVariables[temp_list[i]] = []
            triple_styles[-1].append("")
        else:
            found = False
            for t in prefixes:
                if temp_list[i].startswith(t):
                    triple_styles[-1].append(t)
                    found = True
                    break
            if not found:
                triple_styles[-1].append("other")
    elif i<len(temp_list)-1:
        triples.append([])
        triple_styles.append([])
"""

##### BEGIN SEARCHING #####

conn = sqlite3.connect(args[1])
c = conn.cursor()

checkPrefixes()

for i in range(len(triples)):
    tablenames = getTableNames()
    where = makeWhere(triples[i])
    for tablename in tablenames:
        for row in c.execute('SELECT * FROM '+tablename + where):
            for y in range(len(triples[i])):
                if triples[i][y].startswith("?"):
                    allVariables[triples[i][y]].append(str(row[y]))

conn.commit()
conn.close()

## Print

printTable(allVariables,printVariables)
#pd.DataFrame(allVariables)
"""
for x in range(len(printVariables)):
    if printVariables != '*':
        for y in allVariables[x]:
            print y
    #else: for
"""
