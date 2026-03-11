from antlr4 import *
from lib.tsql.TSqlLexer import TSqlLexer
from lib.tsql.TSqlParser import TSqlParser
from lib.tsql.TSqlParserVisitor import TSqlParserVisitor
from antlr4.TokenStreamRewriter import TokenStreamRewriter


class ImplicitToAnsiJoinVisitor(TSqlParserVisitor):
    def __init__(self, tokens: CommonTokenStream):
        # Using a token stream rewriter to help with rewriting text.
        self.rewriter = TokenStreamRewriter(tokens)
        # Data structure to hold table sources and join conditions.
        self.table_sources = []  # list of (table_text, alias) tuples
        self.join_conditions = []  # list of join condition texts
        self.filter_conditions = []  # other conditions

    def visitTable_sources(self, ctx: TSqlParser.Table_sourcesContext):
        # Assume table_sources rule returns a list of table_source nodes
        for table_ctx in ctx.getChildren():
            # Navigate to table_source_item
            # (The details depend on your grammar.)
            table_text = table_ctx.getText()  # This might include alias too.
            alias = None
            # If the grammar permits an alias (via as_table_alias), extract it.
            if hasattr(table_ctx, "as_table_alias") and table_ctx.as_table_alias() is not None:
                alias = table_ctx.as_table_alias().getText().strip()
            self.table_sources.append((table_text, alias))
        return self.visitChildren(ctx)

    def visitSearch_condition(self, ctx: TSqlParser.Search_conditionContext):
        # Walk the search_condition tree and collect join conditions:
        # For example, if a node looks like "T1.col = T2.col", it is likely a join condition.
        # (You would examine its children and check if both sides are fully qualified column names
        # that refer to different table aliases.)
        # This example is oversimplified.
        cond_text = ctx.getText()
        if "=" in cond_text:
            # Simple heuristic: if the condition has two dot-separated identifiers, consider it a join condition.
            if cond_text.count('.') >= 2:
                self.join_conditions.append(cond_text)
            else:
                self.filter_conditions.append(cond_text)
        else:
            self.filter_conditions.append(cond_text)
        return self.visitChildren(ctx)

    def rewriteQuery(self, tree: ParserRuleContext):
        # This method uses the information we've collected to perform rewriting.
        # 1. Remove the implicit join comma from the FROM clause.
        # 2. Rewrite the FROM clause to use JOIN keywords and insert appropriate ON join conditions.
        #
        # For instance, if self.table_sources = [(T1, 'T1'), (T2, 'T2'), ...] and join_conditions holds one join condition,
        # you might want to produce:
        #   FROM T1 JOIN T2 ON <join_condition> 
        #
        # Then, remove the join condition from the WHERE clause.
        #
        # With TokenStreamRewriter you can insert text at desired tokens.
        #
        # The details depend on your parse tree structure.
        #
        # For example:
        from_index = tree.getChildIndex( tree.getChild( tree.getChildCount()-2 ) )  # not real code!
        new_from = ""
        if len(self.table_sources) >= 2:
            first_table, first_alias = self.table_sources[0]
            new_from = first_table  # Use original text for the first table
            for (table_text, alias) in self.table_sources[1:]:
                # For illustration, assume we choose the first join condition
                if self.join_conditions:
                    join_cond = self.join_conditions.pop(0)
                else:
                    join_cond = "1=1"  # fallback: CROSS JOIN
                new_from += f" JOIN {table_text} ON {join_cond}"
        # Then use self.rewriter.replace(...) or insertAfter(...) to replace the FROM clause text.
        # Similarly, remove the join conditions from the WHERE clause.
        #
        # Finally, return self.rewriter.getText()
        return self.rewriter.getText()

# Usage:
input_stream = FileStream("query.sql", encoding="utf-8")
lexer = TSqlLexer(input_stream)
token_stream = CommonTokenStream(lexer)
parser = TSqlParser(token_stream)
tree = parser.tsql_file()  # Or your appropriate start rule

visitor = ImplicitToAnsiJoinVisitor(token_stream)
visitor.visit(tree)  # Walk the tree to collect information.
new_query = visitor.rewriteQuery(tree)
print(new_query)
