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

def printTable(variables,printVars):
    if printVars[0] == '*':
        printVars = []
        for e in variables:
            print e
            printVars.append(e)
    sep = '|| '
    printList = [sep]*(len(variables[max(variables, key= lambda y: len(set(variables[y])))])+2)
    for a in printVars:
        print a
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

def fillEmptyRows():
    global allVariables
    for i in allVariables:
        if len(allVariables[i])<len(max(variables[a], key=len)):
            allVariables[i].append(None)

def removeRow(number):
    global allVariables
    if row>=len(allVariables('row')):
        return
    for i in allVariables:
        del allVariables[i][number]


##### START OF MAIN CODE #####

args  = sys.argv
if len(args) != 3:
    error("Expected 'python q8.py <db file> <query file>'")

prefixes = {'other':'NULL'}
printVariables = []
allVariables = {'row':[]} # variable object example: "?city:['dbr:Edmonton','dbr:Calgary']"
triples = []

with open(args[2], 'r') as queryFile:
    text=queryFile.read()


for e in re.findall(r"prefix\s+(.+:)\s*(<[^\s]+>)",text,re.I):
    prefixes[e[0]] = e[1]

printVariables = re.search(r"select\s+(.+)where\s+{",text,re.I).group(1).split()
for e in printVariables:
    if e!='*': allVariables[e] = []
temp_list = filter(None,re.search(r"where\s+\{\s*([^\}]+)\}",text,re.I).group(1).split('\n'))
#print temp_list
#filter\s*regex\((.*),\s*(.*)\)
triples = []
triple_styles = []
regFilter = []
opFilter = []
# [('Filter',position)]
order = []

for i in range(len(temp_list)):
    if temp_list[i].split()[-1] != '.':
        if (i < len(temp_list)): error("missing . at end of line:"+str(temp_list[i]))
        else: temp_list[i] += ' . '
    x = re.findall(r"filter\s*regex\((.*),\s*(.*)\)",temp_list[i],re.I)
    if x != []:
        if not x[0][0].startswith('?'): error("line not formatted properly:"+str(temp_list[i]))
        regFilter.append(list(x[0]))
        order.append(['reg',len(regFilter)-1])
        continue
    x = re.findall(r"filter\s*regex\((.*)\)\s*",temp_list[i],re.I)
    if x != []:
        if not x[0][0].startswith('?'): error("line not formatted properly:"+str(temp_list[i]))
        opFilter.append(x[0].split())
        order.append(['op',len(opFilter)-1])
        continue
    l = temp_list[i].split()
    if len(l) == 4:
        del l[-1]
        triples.append(l)
        triple_styles.append([])
        for e in l:
            if e.startswith('?'):
                allVariables[e] = []
                triple_styles[-1].append("")
            else:
                found = False
                for t in prefixes:
                    if e.startswith(t):
                        triple_styles[-1].append(t)
                        found = True
                        break
                if not found:
                    triple_styles[-1].append("other")
        order.append(['triple',len(triples)-1])
        continue
    error("invalid formatting of line: "+str(temp_list[i]))

##### BEGIN SEARCHING #####

conn = sqlite3.connect(args[1])
c = conn.cursor()

checkPrefixes()

for x in range(len(order)):
    kind = order[x][0]
    i = order[x][1]
    if kind == 'triple':
        tablenames = getTableNames()
        where = makeWhere(triples[i])
        for tablename in tablenames:
            for row in c.execute('SELECT * FROM '+tablename + where):
                tripRow = []
                toRemove = []
                for y in range(len(triples[i])):
                    if triples[i][y].startswith("?"):
                        tripRow.append([triples[y],str(row[y])])
                    else:
                        tripRow.append(['row',None])
                for z in len(allVariables.row):
                    aV1,aV2,aV3 = allVariables[tripRow[0][0]][z], allVariables[tripRow[1][0]][z], allVariables[tripRow[2][0]][z]

                    if (aV1 != tripRow[0][1] and aV1==None) or (aV2 != tripRow[0][1] and aV2==None) or (aV3 != tripRow[0][1] and aV2==None):

                    elif not ((aV1 == tripRow[0][1]) and (aV2 == tripRow[0][1]) and (aV3 == tripRow[0][1])):
                        toRemove.append(z)
                        break
                    allVariables[triples[i][y]].append(str(row[y]))
    elif kind == 'op':
        #for e in allVariables[opFilter[i][0]]:
        #
        pass
    elif kind == 'reg':
        for e in allVariables[regFilter[i][0]]:
            print regFilter[i]
        pass


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
