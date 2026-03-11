from antlr4 import ParseTreeListener
from lib.tsql.TSqlParserListener import TSqlParserListener
from lib.tsql.TSqlParser import TSqlParser

class TableColumnExtractor(TSqlParserListener):
    def __init__(self):
        # Mapping: key = table name (could be original or alias) -> list of column names
        self.table_column_map = {}
        # Global mapping: alias -> original table name
        self.alias_map = {}
        # Current original table name in context (for unqualified columns)
        self.current_original_table = None

    def enterTable_source_item(self, ctx: TSqlParser.Table_source_itemContext):
        # Extract original table name from full_table_name (e.g. if "dbo.CURRENCIES", take "CURRENCIES")
        self.current_original_table = None
        if hasattr(ctx, "full_table_name") and ctx.full_table_name() is not None:
            full_table_text = ctx.full_table_name().getText()
            tokens = [t for t in full_table_text.split('.') if t]
            if tokens:
                original = tokens[-1]
                self.current_original_table = original
                if original not in self.table_column_map:
                    self.table_column_map[original] = []
                print(f"Detected original table: {original}")

        # Check for alias using as_table_alias
        if hasattr(ctx, "as_table_alias") and ctx.as_table_alias() is not None:
            alias_text = ctx.as_table_alias().getText()
            parts = alias_text.split()
            alias = parts[-1] if parts else alias_text
            if self.current_original_table:
                # Record the alias mapping globally.
                self.alias_map[alias] = self.current_original_table
                # Also create a key for the alias, because column references may fall under that key.
                if alias not in self.table_column_map:
                    self.table_column_map[alias] = []
                print(f"Mapping alias '{alias}' to original table '{self.current_original_table}'")

    def exitTable_source_item(self, ctx: TSqlParser.Table_source_itemContext):
        self.current_original_table = None

    def enterFull_column_name(self, ctx: TSqlParser.Full_column_nameContext):
        full_col_text = ctx.getText().strip()
        parts = full_col_text.split('.')
        if len(parts) == 2:
            qualifier, column_name = parts[0], parts[1]
            if qualifier in self.alias_map:
                original_table = self.alias_map[qualifier]
                print(f"Qualified column '{column_name}' using alias '{qualifier}' resolved to table '{original_table}'")
            else:
                original_table = qualifier
                print(f"Qualified column '{column_name}' associated with table '{original_table}'")
            if original_table not in self.table_column_map:
                self.table_column_map[original_table] = []
            self.table_column_map[original_table].append(column_name)
        else:
            # Unqualified column: if we have a current table context, assign to it.
            if self.current_original_table:
                self.table_column_map[self.current_original_table].append(full_col_text)
                print(f"Unqualified column '{full_col_text}' assigned to table '{self.current_original_table}'")
            else:
                print(f"Warning: Unqualified column '{full_col_text}' with no table context.")

    def getRawMapping(self):
        return self.table_column_map

    def postProcessMapping(self):
        """
        For every key in alias_map, merge the columns from that alias key into the original table key.
        Then remove the alias key from the mapping.
        Also remove duplicate columns.
        """
        # Merge alias keys into their original table's entry.
        for alias, orig in self.alias_map.items():
            if alias in self.table_column_map:
                if orig not in self.table_column_map:
                    self.table_column_map[orig] = []
                # Merge: add all alias columns into original table columns.
                self.table_column_map[orig].extend(self.table_column_map[alias])
                print(f"Merging columns from alias '{alias}' into original table '{orig}'")
                # Remove the alias key.
                del self.table_column_map[alias]

        # Remove duplicate columns from each table while preserving order.
        for table in self.table_column_map:
            seen = set()
            unique_cols = []
            for col in self.table_column_map[table]:
                if col not in seen:
                    unique_cols.append(col)
                    seen.add(col)
            self.table_column_map[table] = unique_cols

        return self.table_column_map

    def getTableColumnMap(self):
        return self.table_column_map
