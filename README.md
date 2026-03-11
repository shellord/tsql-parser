# tsql-parser

Small Python prototype for parsing T-SQL with ANTLR4 and extracting a table-to-column usage map from a SQL file.

## What it does

The current Python workflow is centered on [`parse.py`](/Users/saheenshoukath/dev/projects/tsql-parser/parse.py) and [`listener.py`](/Users/saheenshoukath/dev/projects/tsql-parser/listener.py):

- Reads SQL from [`query.sql`](/Users/saheenshoukath/dev/projects/tsql-parser/query.sql)
- Replaces report-style placeholders like `$P{RA_COMP}` with a neutral token before parsing
- Parses the query using the generated ANTLR T-SQL lexer/parser in [`lib/tsql`](/Users/saheenshoukath/dev/projects/tsql-parser/lib/tsql)
- Walks the parse tree with a custom listener
- Builds a mapping of table names to referenced columns
- Resolves table aliases back to the original table name
- Deduplicates columns before printing the final result

In practice, this is useful when you want a quick dependency view of which columns are referenced from which tables in a T-SQL statement.

## Project structure

- [`parse.py`](/Users/saheenshoukath/dev/projects/tsql-parser/parse.py): entry point that loads the SQL, parses it, walks the tree, and prints the final mapping
- [`listener.py`](/Users/saheenshoukath/dev/projects/tsql-parser/listener.py): custom ANTLR listener that collects tables, aliases, and column references
- [`query.sql`](/Users/saheenshoukath/dev/projects/tsql-parser/query.sql): input SQL file parsed by the script
- [`lib/tsql`](/Users/saheenshoukath/dev/projects/tsql-parser/lib/tsql): generated T-SQL lexer/parser files and upstream grammar assets
- [`ansii.py`](/Users/saheenshoukath/dev/projects/tsql-parser/ansii.py): separate experimental visitor intended to rewrite implicit joins to ANSI joins

## How the extractor works

`TableColumnExtractor` listens for two main parse events:

- `enterTable_source_item`: captures table names from the `FROM` clause and records aliases
- `enterFull_column_name`: captures qualified column references such as `a.col`

Alias handling works like this:

- If a table appears as `dbo.TableA a`, the listener records `a -> TableA`
- When it later sees `a.column1`, it attributes that column to `TableA`
- After the parse walk completes, alias buckets are merged into the original table entry

For unqualified columns, the listener attempts to assign them to the current table context. That behavior is heuristic and works best for simpler statements.

## Requirements

The Python code expects:

- Python 3
- `antlr4-python3-runtime`

The repository already includes generated parser files, so you do not need to regenerate the grammar just to run the extractor.

## Running it

Install the ANTLR runtime if needed:

```bash
pip install antlr4-python3-runtime
```

Run the parser from the repository root:

```bash
python parse.py
```

The script prints output in this shape:

```text
Final Mapping (Original Table Names, Unique Columns):
Original Table: CTSTRS
  Column: TRS_DATE
  Column: VALUE_DATE
```

## Input assumptions

- The script always reads from `query.sql`
- Placeholder expressions matching `$P{...}` are replaced before parsing
- The extractor is aimed at `SELECT`-style queries with table aliases and column references
- Results are printed to stdout; nothing is written to a file

## Limitations

- This is currently a script, not a packaged library or CLI tool
- Unqualified columns may be assigned ambiguously
- More complex T-SQL constructs may need additional listener logic
- [`ansii.py`](/Users/saheenshoukath/dev/projects/tsql-parser/ansii.py) appears to be exploratory and is not integrated into the main workflow

