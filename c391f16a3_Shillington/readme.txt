Noah Shillington
I did not collaborate with anyone for this assignment.

q6's db is called "q6.db", and the example RDF graph is called "q6_exampleRDF_lamp.txt"

Q8) needs sqlite3 and sys python2.7 libraries to run.
	to execute: python q8.py <db file> <RDF Turtle file> 
	or: 	    python2.7 q8.py <db file> <RDF Turtle file>
	
	to import the example turtles:
		python q8.py q8.db Edmonton.txt
		python q8.py q8.db q6_exampleRDF_lamp.txt

Q9) needs sqlite3, sys, and re python2.7 libraries to run.
	to execute: python q9.py <db file> <query file>
	or: 	    python2.7 q9.py <db file> <query file>

	for example:
		python q9.py q8.db q9_query_all.txt

The example RDF is called "q6_exampleRDF_lamp.txt"
It's .db is called "q6.db"
It's test queries begin with "q9_query_"
The file q8.db has the RDFs of "Edmonton.txt" and "q6_exampleRDF_lamp.txt"