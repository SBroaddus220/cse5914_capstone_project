# -*- coding: utf-8 -*-

"""
Interface for the SQLite database.
"""

# **** IMPORTS ****
import logging
import sqlite3
import sqlparse
from pathlib import Path
from typing import Any, Dict, List, Tuple

# **** LOGGING ****
logger = logging.getLogger(__name__)

# **** FUNCTIONS ****
def get_db_connection(db_path: Path) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database.

    Args:
        db_path (Path): Path to the SQLite database file.

    Returns:
        sqlite3.Connection: Connection object to the SQLite database.
    """
    logger.info(f"Connecting to database at {db_path}")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def get_foreign_keys(conn: sqlite3.Connection, table: str) -> List[Tuple[str, str, str, str]]:
    """Retrieve foreign key relationships for a given table.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Table name.

    Returns:
        List[Tuple[str, str, str, str]]: List of (from_table, from_column, to_table, to_column).
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    return [(ref[2], ref[3], table, ref[4]) for ref in cursor.fetchall()]


def find_referencing_rows(
    conn: sqlite3.Connection, table: str, column: str, value: Any
) -> Dict[str, List[Tuple]]:
    """Find all rows that reference a given row.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Target table name.
        column (str): Target column name.
        value (Any): Value to search for.

    Returns:
        Dict[str, List[Tuple]]: Mapping of referencing table names to lists of matching rows.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table})")
    references = cursor.fetchall()

    results = {}
    
    for ref in references:
        from_table = ref[2]  # Table that references this table
        from_column = ref[3]  # Column in the referencing table

        query = f"SELECT * FROM {from_table} WHERE {from_column} = ?"
        rows = cursor.execute(query, (value,)).fetchall()

        if rows:
            results[from_table] = rows
    
    return results


def find_referenced_rows(conn: sqlite3.Connection, table: str, row_id: Any) -> Dict[str, List[Tuple]]:
    """Find rows that a given row references.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Source table name.
        row_id (Any): ID of the row to check.

    Returns:
        Dict[str, List[Tuple]]: Mapping of referenced table names to lists of matching rows.
    """
    cursor = conn.cursor()
    foreign_keys = get_foreign_keys(conn, table)

    results = {}

    for from_table, from_column, to_table, to_column in foreign_keys:
        # Get the value of the foreign key column in the given row
        cursor.execute(f"SELECT {from_column} FROM {from_table} WHERE id = ?", (row_id,))
        result = cursor.fetchone()

        if result and result[0] is not None:
            ref_value = result[0]
            query = f"SELECT * FROM {to_table} WHERE {to_column} = ?"
            referenced_rows = cursor.execute(query, (ref_value,)).fetchall()

            if referenced_rows:
                results[to_table] = referenced_rows

    return results

def extract_table_names(sql: str) -> List[str]:
    """Extracts table names from an SQL statement.

    Args:
        sql (str): The SQL query.

    Returns:
        List[str]: A list of table names found in the query.
    """
    parsed = sqlparse.parse(sql)
    tables = set()

    for statement in parsed:
        for token in statement.tokens:
            if token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
                tables.add(token.get_real_name())

    return list(tables)

def find_sibling_rows(conn: sqlite3.Connection, table: str, row_id: Any) -> Dict[str, List[Tuple]]:
    """Find rows that share the same parent as a given row.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        table (str): Table to check for siblings.
        row_id (Any): ID of the row whose siblings are sought.

    Returns:
        Dict[str, List[Tuple]]: Mapping of parent tables to lists of sibling rows.
    """
    cursor = conn.cursor()
    foreign_keys = get_foreign_keys(conn, table)

    results = {}

    for from_table, from_column, to_table, to_column in foreign_keys:
        # Get the parent's ID for the given row
        cursor.execute(f"SELECT {from_column} FROM {from_table} WHERE id = ?", (row_id,))
        result = cursor.fetchone()

        if result and result[0] is not None:
            parent_id = result[0]

            # Find other rows in the same table with the same parent
            query = f"SELECT * FROM {from_table} WHERE {from_column} = ? AND id != ?"
            siblings = cursor.execute(query, (parent_id, row_id)).fetchall()

            if siblings:
                results[from_table] = siblings

    return results



def get_foreign_keys_from_sql(conn: sqlite3.Connection, sql: str) -> Dict[str, List[Tuple[str, str, str, str]]]:
    """Finds foreign key relationships for tables involved in an SQL query.

    Args:
        conn (sqlite3.Connection): SQLite database connection.
        sql (str): The SQL query.

    Returns:
        Dict[str, List[Tuple[str, str, str, str]]]: Mapping of tables to their foreign key relationships.
    """
    table_names = extract_table_names(sql)
    foreign_keys = {}

    for table in table_names:
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA foreign_key_list({table})")
            keys = [(ref[2], ref[3], table, ref[4]) for ref in cursor.fetchall()]

            if keys:
                foreign_keys[table] = keys
        except sqlite3.OperationalError:
            continue  # Ignore errors if the table does not exist

    return foreign_keys

import sqlite3
from typing import Dict, List, Tuple, Any, Union

def find_parent_child_rows(
    conn: sqlite3.Connection,
    original_sql: str,
    clicked_row: int,
    related_queries: List[str]
) -> Dict[str, Any]:
    """Find rows in related queries that reference or are referenced by a clicked row.

    This function:
      1) Identifies which tables from the original_sql might match the clicked_row
         if that row corresponds to an INTEGER PRIMARY KEY in any table.
      2) For each matched table, searches all related_queries for:
         - Child rows referencing the matched table's rows.
         - Parent rows referenced by the matched table's rows.

    Args:
        conn (sqlite3.Connection): The SQLite database connection.
        original_sql (str): The SQL query from which a row was clicked.
        clicked_row (int): The number corresponding to the row that was clicked.
        related_queries (List[str]): Additional SQL queries to evaluate.

    Returns:
        Dict[str, Any]: A mapping containing:
          - 'matched_tables': Tables from the original_sql matching clicked_row as a PK.
          - 'matched_queries': Related queries that reference matched tables.
          - 'children': Rows in related_queries referencing matched rows.
          - 'parents': Rows in related_queries referenced by matched rows.
    """

    def tables_with_clicked_row_as_pk(
        connection: sqlite3.Connection,
        sql: str,
        row_id: int
    ) -> List[str]:
        """Returns a list of tables from the given SQL where row_id exists as an INTEGER PRIMARY KEY."""
        matched = []
        tables = extract_table_names(sql)
        for tbl in tables:
            try:
                # Identify an INTEGER PRIMARY KEY column if it exists
                c = connection.cursor()
                c.execute(f"PRAGMA table_info({tbl})")
                cols_info = c.fetchall()
                pk_cols = [col[1] for col in cols_info if col[5] == 1]  # pk=1
                # If there's no declared primary key, we might attempt rowid
                # but we focus on explicitly declared PK for this example.
                for pk_col in pk_cols:
                    # Attempt to see if row_id matches a row in this table
                    c.execute(f"SELECT 1 FROM {tbl} WHERE {pk_col} = ? LIMIT 1", (row_id,))
                    if c.fetchone():
                        matched.append(tbl)
                        break
            except sqlite3.OperationalError:
                continue
        return matched

    # Step 1: Identify which tables from original_sql match clicked_row as an INTEGER PK
    matched_tables = tables_with_clicked_row_as_pk(conn, original_sql, clicked_row)

    # Prepare container
    results: Dict[str, Any] = {
        "matched_tables": matched_tables,
        "matched_queries": [],
        "children": {},
        "parents": {}
    }

    if not matched_tables:
        return results

    # For each related query, gather foreign keys, then check referencing
    for query in related_queries:
        fk_map = get_foreign_keys_from_sql(conn, query)
        query_children = []
        query_parents = []

        # For each table in fk_map, we have a list of fkeys
        # (parent_table, parent_key, child_table, child_key)
        for table, fkeys in fk_map.items():
            for parent_table, child_key, child_table, parent_key in fkeys:

                # Check if child_table is one of the matched_tables
                if child_table in matched_tables:
                    # For each matched table, we see if row with PK=clicked_row references parent_table
                    # i.e., original_table -> parent_table
                    c = conn.execute(
                        f"SELECT {child_key} FROM {child_table} WHERE {child_key} IS NOT NULL AND rowid IS NOT NULL"
                    )
                    ref_values = c.fetchall()
                    # If clicked_row is an actual PK in child_table, get the referencing column value
                    col_cursor = conn.execute(
                        f"SELECT {child_key} FROM {child_table} WHERE {child_key} = ?",
                        (clicked_row,)
                    )
                    val = col_cursor.fetchone()
                    if val:
                        # Use val to find matching rows in parent_table
                        parent_rows = conn.execute(
                            f"SELECT * FROM {parent_table} WHERE {parent_key} = ?",
                            (val[0],)
                        ).fetchall()
                        query_parents.extend(parent_rows)
                        results["matched_queries"].append(query)
                        results["parents"][query] = {
                            "matched_table": child_table,
                        }

                # Check if parent_table is one of the matched_tables
                if parent_table in matched_tables:
                    # For each matched table, if we have PK=clicked_row, see if there's a referencing row in child_table
                    # i.e., child_table -> original_table
                    c = conn.execute(
                        f"SELECT * FROM {parent_table} WHERE rowid IS NOT NULL"
                    )
                    # Attempt to see if row with PK=clicked_row is in parent_table
                    row_check = conn.execute(
                        f"SELECT 1 FROM {parent_table} WHERE {parent_key} = ? LIMIT 1",
                        (clicked_row,)
                    ).fetchone()
                    if row_check:
                        children_rows = conn.execute(
                            f"SELECT * FROM {child_table} WHERE {child_key} = ?",
                            (clicked_row,)
                        ).fetchall()
                        query_children.extend(children_rows)
                        results["matched_queries"].append(query)
                        results["children"][query] = {
                            "matched_table": parent_table,
                        }
                
                if child_table not in results["matched_tables"]:
                    results["matched_tables"].append(child_table)
                if parent_table not in results["matched_tables"]:
                    results["matched_tables"].append(parent_table)

        if query_children:
            # results["children"][query]["matched_rows"] = query_children
            results["children"][query]["matched_rows"] = [dict(row) for row in query_children]
        if query_parents:
            # results["parents"][query]["matched_rows"] = query_parents
            results["parents"][query]["matched_rows"] = [dict(row) for row in query_parents]

    return results


def backup_database(source_db_conn: sqlite3.Connection, destination_db_path: Path) -> None:
    """Copies the source database to the destination path.

    Args:
        source_db_conn (sqlite3.Connection): Connection to the source database.
        destination_db_path (Path): Path to the destination database.
    """
    logger.info(f"Backing up database at {source_db_conn} to {destination_db_path}")
    backup_conn = get_db_connection(destination_db_path)
    source_db_conn.backup(backup_conn)

# ****
if __name__ == "__main__":
    raise Exception("This file is not meant to run on its own.")
    