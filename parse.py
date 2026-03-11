from antlr4 import *
from lib.tsql.TSqlLexer import TSqlLexer
from lib.tsql.TSqlParser import TSqlParser
from listener import TableColumnExtractor
import re

def pre_process_query(query):
    query = re.sub(r'\$P\{[^}]+\}', 'PLACEHOLDER', query)
    return query

with open("query.sql", "r") as file:
    input_stream = InputStream(pre_process_query(file.read()))

# Create the lexer and token stream
lexer = TSqlLexer(input_stream)
token_stream = CommonTokenStream(lexer)

# Create the parser using the tokens from the lexer
parser = TSqlParser(token_stream)

# Parse the input starting from the initial grammar rule (e.g., "tsql_file")
tree = parser.tsql_file()
# print(tree.toStringTree(recog=parser))


# Instantiate the custom listener
extractor = TableColumnExtractor()

# Walk the parse tree with the custom listener
walker = ParseTreeWalker()
walker.walk(extractor, tree)





final_mapping = extractor.postProcessMapping()
print("\nFinal Mapping (Original Table Names, Unique Columns):")
for table, cols in final_mapping.items():
    print(f"Original Table: {table}")
    for col in cols:
        print(f"  Column: {col}")