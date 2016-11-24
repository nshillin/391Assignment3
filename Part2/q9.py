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
        try_query('SELECT uri FROM prefix WHERE uri=?',(prefixes[i],))
        uri = c.fetchone()[0]
        if uri == None: error("uri not found: " + uri)

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
        elif len(allVariables[triple[y]])>0 and allVariables[triple[y]][0] != None and len(set(allVariables[triple[y]]))>1:
            where += '('
            for value in allVariables[triple[y]]:
                if value == None: continue
                if '/' in value:
                    if '#' in value:
                        pos = value.rfind('#')
                    else:
                        pos = value.rfind('/')
                    value = value[pos+1:]
                where += types[y]+'="'+value+'" or '
            where = where[:-4] + ') and '
    return where[:-4]

def replacePrefixes():
    flippedDict = {v: k for k, v in prefixes.iteritems()}
    for i in allVariables:
        for j in range(len(allVariables[i])):
            value = allVariables[i][j]
            if value == None or '/' not in value: continue
            if '#' in value:
                pos = value.rfind('#')
            else:
                pos = value.rfind('/')
            value_start = ['<',value[:pos+1],'>']
            if ''.join(value_start) in flippedDict and flippedDict[''.join(value_start)] != 'other':
                allVariables[i][j] = value.replace(value_start[1],flippedDict[''.join(value_start)])




def printTable(variables,printVars):
    replacePrefixes()
    printVars = ['row']+printVars
    if printVars[1] == '*':
        printVars = []
        for e in variables:
            if e != 'row': printVars = [e] + printVars
        printVars = ['row'] + printVars
    for i in range(len(variables['row'])):
        variables['row'][i] = str(i+1)
    sep = '|| '
    printList = [sep]*(len(variables[max(variables, key= lambda y: len(set(variables[y])))])+2)
    for a in printVars:
        for x in range(len(variables[a])):
            if variables[a][x] == None:
                variables[a][x] = ''
        width = len(a)+1
        if len(variables[a])>0 and len(max(variables[a], key=len))+1 > width:
            width = len(max(variables[a], key=len))+1
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
        while len(allVariables[i])<len(allVariables[max(allVariables, key=lambda x:len(allVariables[x]))]):
            allVariables[i].append(None)


def removeRow(number):
    global allVariables
    if number>=len(allVariables['row']):
        return
    for i in allVariables:
        del allVariables[i][number]

##### START OF MAIN CODE #####

args  = sys.argv
if len(args) != 3:
    error("Expected 'python q8.py <db file> <query file>'")

prefixes = {'other':'<>'}
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
    s = temp_list[i].split()
    if len(s)==0:
        continue
    if s[-1] != '.':
        if (i < len(temp_list)): error("missing '.' at end of line: "+str(temp_list[i]))
        else: temp_list[i] += ' . '
    x = re.findall(r"filter\s+regex\((.+)\s*,\s*(.+)\)",temp_list[i],re.I)
    if x != []:
        if not x[0][0].startswith('?'): error("line not formatted properly: "+str(temp_list[i]))
        regFilter.append(list(x[0]))
        regFilter[-1][1] = regFilter[-1][1][1:-1]
        order.append(['reg',len(regFilter)-1])
        continue
    x = re.findall(r"filter\s*\(([^<>!=]+)\s*([<>!=]{1,2})\s*([\-\.\d]+)\)",temp_list[i],re.I)
    if x != []:
        if not x[0][0].startswith('?'): error("line not formatted properly: "+str(temp_list[i]))
        opFilter.append(list(x[0]))
        try: opFilter[-1][2] = float(opFilter[-1][2])
        except: error("Not a number: " + opFilter[-1][2])
        order.append(['op',len(opFilter)-1])
        continue
    l = temp_list[i].split()
    if len(l) == 4:
        del l[-1]
        triples.append(l)
        triple_styles.append([])
        for e in range(len(triples[-1])):
            if triples[-1][e].startswith('?'):
                allVariables[triples[-1][e]] = []
                triple_styles[-1].append("")
            else:
                found = False
                for t in prefixes:
                    if triples[-1][e].startswith(t):
                        triple_styles[-1].append(prefixes[t])
                        triples[-1][e] = triples[-1][e].replace(t,'')
                        found = True
                        break
                if not found:
                    if triples[-1][e][0] == '<' and triples[-1][e][-1] == '>':
                        if '#' in triples[-1][e]:
                            pos = triples[-1][e].rfind('#')
                        else:
                            pos = triples[-1][e].rfind('/')
                        triple_styles[-1].append(triples[-1][e][:pos+1]+'>')
                        triples[-1][e] = triples[-1][e][pos+1:-1]
                    else:
                        triple_styles[-1].append("other")
        order.append(['triple',len(triples)-1])
        continue
    error("invalid formatting of line: "+str(temp_list[i]))
##### BEGIN SEARCHING #####

conn = sqlite3.connect(args[1])
c = conn.cursor()

checkPrefixes()

empty = True
for x in range(len(order)):
    kind = order[x][0]
    i = order[x][1]
    if kind == 'triple':
        tablenames = getTableNames()
        where = makeWhere(triples[i])
        if empty:
            for tablename in tablenames:
                titles = tablename[2:-1].replace('>','').split('<')
                for row in c.execute('SELECT * FROM '+tablename + where):
                    for y in range(len(triples[i])):
                        if triples[i][y].startswith("?"):
                            allVariables[triples[i][y]].append(titles[y]+str(row[y].encode('utf-8')))
                fillEmptyRows()
                empty = False
        else:
            doNotRemove = []
            for tablename in tablenames:
                titles = tablename[2:-1].replace('>','').split('<')
                for row in c.execute('SELECT * FROM '+tablename + where):
                    tripRow = []
                    for y in range(len(triples[i])):
                        if triples[i][y].startswith("?"):
                            tripRow.append([triples[i][y],str(row[y].encode('utf-8'))])
                        else:
                            tripRow.append(['row',None])
                    for num in range(len(tripRow)):
                        if tripRow[num][1] != None: tripRow[num][1] = titles[num] + tripRow[num][1]
                    for t in range(len(tripRow)):
                        if tripRow[t][1] == None or tripRow[t][0] == 'row':
                            continue
                        elif None in allVariables[tripRow[t][0]]:
                            for z in range(len(allVariables['row'])):
                                if (allVariables[tripRow[(t+1)%3][0]][z] == tripRow[(t+1)%3][1]) and (allVariables[tripRow[(t+2)%3][0]][z] == tripRow[(t+2)%3][1]) and allVariables[tripRow[t][0]][z] == None:
                                    allVariables[tripRow[t][0]][z] = tripRow[t][1]
                                    allVariables[tripRow[(t+1)%3][0]].append(allVariables[tripRow[(t+1)%3][0]][z])
                                    allVariables[tripRow[(t+2)%3][0]].append(allVariables[tripRow[(t+2)%3][0]][z])
                                    fillEmptyRows()
                    for z in range(len(allVariables['row'])-1,-1,-1):
                        aV1,aV2,aV3 = allVariables[tripRow[0][0]][z], allVariables[tripRow[1][0]][z], allVariables[tripRow[2][0]][z]
                        #print aV1, tripRow[0][1]
                        #print aV2, tripRow[1][1]
                        #print aV3, tripRow[2][1]
                        if (aV1 == tripRow[0][1]) and (aV2 == tripRow[1][1]) and (aV3 == tripRow[2][1]):
                            doNotRemove.append(z)
                            continue
            for z in range(len(allVariables['row'])-1,-1,-1):
                if z not in doNotRemove:
                    removeRow(z)
    elif kind == 'op':
        print opFilter[i]
        #for e in allVariables[opFilter[i][0]]:
        #
        pass
    elif kind == 'reg':
        for row in range(len(allVariables[regFilter[i][0]])-1,-1,-1):
            if allVariables[regFilter[i][0]][row] == None or (regFilter[i][1].lower() not in allVariables[regFilter[i][0]][row].lower()):
                removeRow(row)

conn.commit()
conn.close()

## Print

printTable(allVariables,printVariables)
#pd.DataFrame(allVariables)
