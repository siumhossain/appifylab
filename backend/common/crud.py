from typing import Any, Dict, List, Optional, Union, TypeVar
from sqlalchemy import text
from sqlalchemy.orm import Session

T = TypeVar('T')


class DatabaseCRUD:

    def __init__(self, db: Session):
        if not db:
            raise ValueError("Database connection is required")
        self.db = db

    def create(
        self,
        table_name: str,
        data: Dict[str, Any],
        returning: Union[str, List[str]] = "*"
    ) -> Dict[str, Any]:
        
        try:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ", ".join([f":p{i}" for i in range(len(columns))])
            column_names = ", ".join(columns)

            returning_clause = ", ".join(returning) if isinstance(returning, list) else returning

            query = f"""
                INSERT INTO {table_name} ({column_names})
                VALUES ({placeholders})
                RETURNING {returning_clause}
            """

            params = {f"p{i}": v for i, v in enumerate(values)}
            result = self.db.execute(text(query), params)
            self.db.commit()
            row = result.fetchone()
            return dict(row._mapping) if row else None
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Create operation failed: {str(e)}")

    def find_first(
        self,
        table_name: str,
        conditions: Dict[str, Any],
        fields: Union[str, List[str]] = "*"
    ) -> Optional[Dict[str, Any]]:
        try:
            selected_fields = ", ".join(fields) if isinstance(fields, list) else fields
            where_clause, params = self._build_where_clause(conditions)

            query = f"""
                SELECT {selected_fields} FROM {table_name}
                WHERE {where_clause}
                LIMIT 1
            """

            result = self.db.execute(text(query), params)
            row = result.fetchone()
            return dict(row._mapping) if row else None
        except Exception as e:
            raise Exception(f"Find first failed: {str(e)}")

    def read(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None,
        fields: Union[str, List[str]] = "*",
        options: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        try:
            options = options or {}
            conditions = conditions or {}
            selected_fields = ", ".join(fields) if isinstance(fields, list) else fields
            where_clause, params = self._build_where_clause(conditions)

            query = f"SELECT {selected_fields} FROM {table_name}"

            if where_clause:
                query += f" WHERE {where_clause}"

            if options.get("order_by"):
                query += f" ORDER BY {options['order_by']}"

            if options.get("limit"):
                query += f" LIMIT {int(options['limit'])}"

            if options.get("offset"):
                query += f" OFFSET {int(options['offset'])}"

            result = self.db.execute(text(query), params)
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            raise Exception(f"Read operation failed: {str(e)}")

    def update(
        self,
        table_name: str,
        data: Dict[str, Any],
        conditions: Dict[str, Any],
        returning: Union[str, List[str]] = "*",
        text_array_columns: Optional[List[str]] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        try:
            if not conditions:
                raise ValueError(
                    "Update conditions are required to prevent accidental mass updates"
                )

            text_array_columns = text_array_columns or []
            update_columns = list(data.keys())
            update_values = list(data.values())

            set_parts = []
            params = {}
            for i, col in enumerate(update_columns):
                param_name = f"set_{i}"
                val = update_values[i]
                if isinstance(val, list) and col in text_array_columns:
                    set_parts.append(f"{col} = :{param_name}::text[]")
                else:
                    set_parts.append(f"{col} = :{param_name}")
                params[param_name] = val

            set_clause = ", ".join(set_parts)

            where_clause, condition_params = self._build_where_clause(
                conditions, start_index=len(update_values)
            )
            params.update(condition_params)

            returning_clause = ", ".join(returning) if isinstance(returning, list) else returning

            query = f"""
                UPDATE {table_name}
                SET {set_clause}
                WHERE {where_clause}
                RETURNING {returning_clause}
            """

            result = self.db.execute(text(query), params)
            self.db.commit()
            rows = result.fetchall()
            results = [dict(row._mapping) for row in rows]

            return results[0] if len(results) == 1 else results
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Update operation failed: {str(e)}")

    def delete(
        self,
        table_name: str,
        conditions: Dict[str, Any],
        returning: Union[str, List[str]] = "id"
    ) -> List[Dict[str, Any]]:
        try:
            if not conditions:
                raise ValueError(
                    "Delete conditions are required to prevent accidental mass deletions"
                )

            where_clause, params = self._build_where_clause(conditions)
            returning_clause = ", ".join(returning) if isinstance(returning, list) else returning

            query = f"""
                DELETE FROM {table_name}
                WHERE {where_clause}
                RETURNING {returning_clause}
            """

            result = self.db.execute(text(query), params)
            self.db.commit()
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Delete operation failed: {str(e)}")

    def exists(
        self,
        table_name: str,
        conditions: Dict[str, Any]
    ) -> bool:
        try:
            where_clause, params = self._build_where_clause(conditions)

            query = f"""
                SELECT EXISTS(
                    SELECT 1 FROM {table_name}
                    WHERE {where_clause}
                ) as exists
            """

            result = self.db.execute(text(query), params)
            row = result.fetchone()
            return row.exists if row else False
        except Exception as e:
            raise Exception(f"Exists check failed: {str(e)}")

    def count(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        try:
            conditions = conditions or {}
            where_clause, params = self._build_where_clause(conditions)

            query = f"SELECT COUNT(*) as count FROM {table_name}"

            if where_clause:
                query += f" WHERE {where_clause}"

            result = self.db.execute(text(query), params)
            row = result.fetchone()
            return int(row.count) if row else 0
        except Exception as e:
            raise Exception(f"Count operation failed: {str(e)}")

    def get_paginated_list(
        self,
        table_name: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            options = options or {}
            conditions = options.get("conditions", {})
            search_conditions = options.get("search_conditions")
            fields = options.get("fields", "*")
            joins = options.get("joins", [])
            order_by = options.get("order_by", "id DESC")
            size = int(options.get("size", 10))
            cursor = options.get("cursor")
            cursor_field = options.get("cursor_field", "id")

            selected_fields = ", ".join(fields) if isinstance(fields, list) else fields
            where_clause, params = self._build_where_clause(conditions)

            join_clause = " ".join(
                [f"{j['type']} {j['table']} ON {j['on']}" for j in joins]
            )

            query = f"SELECT {selected_fields} FROM {table_name}"

            if join_clause:
                query += f" {join_clause}"

            full_where_clause = where_clause
            param_index = len(params)

            if search_conditions and search_conditions.get("OR"):
                search_parts = []
                for condition in search_conditions["OR"]:
                    field = list(condition.keys())[0]
                    operator_dict = condition[field]
                    operator = list(operator_dict.keys())[0]
                    value = operator_dict[operator]

                    param_name = f"search_{param_index}"
                    param_index += 1

                    if operator == "ILIKE":
                        params[param_name] = value
                        search_parts.append(f"{field} ILIKE :{param_name}")
                    elif operator == "CAST_ILIKE":
                        params[param_name] = value
                        search_parts.append(f"CAST({field} AS TEXT) ILIKE :{param_name}")

                if search_parts:
                    search_clause = f"({' OR '.join(search_parts)})"
                    if full_where_clause:
                        full_where_clause = f"{full_where_clause} AND {search_clause}"
                    else:
                        full_where_clause = search_clause

            if cursor is not None:
                order_by_field = order_by.split()[0]
                is_descending = "DESC" in order_by.upper()
                cursor_operator = "<" if is_descending else ">"

                param_name = f"cursor_{param_index}"
                params[param_name] = cursor

                cursor_condition = f"{order_by_field} {cursor_operator} :{param_name}"

                if full_where_clause:
                    full_where_clause = f"{full_where_clause} AND {cursor_condition}"
                else:
                    full_where_clause = cursor_condition

            if full_where_clause:
                query += f" WHERE {full_where_clause}"

            group_by = options.get("group_by")
            if group_by:
                query += f" GROUP BY {group_by}"

            query += f" ORDER BY {order_by} LIMIT {size + 1}"

            result = self.db.execute(text(query), params)
            rows = result.fetchall()
            results = [dict(row._mapping) for row in rows]

            has_more = len(results) > size
            if has_more:
                results.pop()

            next_cursor = None
            if results:
                last_row = results[-1]
                field_name = cursor_field.split(".")[-1] if "." in cursor_field else cursor_field
                next_cursor = last_row.get(field_name)

            return {
                "data": results,
                "pagination": {
                    "has_more": has_more,
                    "next_cursor": next_cursor if has_more else None,
                    "size": size
                }
            }
        except Exception as e:
            raise Exception(f"Paginated list operation failed: {str(e)}")

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Any:
        try:
            params = params or {}

            if isinstance(options, str):
                options = {"method": options}

            options = options or {}
            method = options.get("method", "many_or_none")
            paginate = options.get("paginate", False)
            size = int(options.get("size", 10))
            cursor = options.get("cursor")
            cursor_field = options.get("cursor_field", "id")
            order_by = options.get("order_by", "id DESC")

            if not paginate:
                result = self.db.execute(text(query), params)

                if method == "one":
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                elif method == "one_or_none":
                    row = result.fetchone()
                    return dict(row._mapping) if row else None
                else:
                    rows = result.fetchall()
                    return [dict(row._mapping) for row in rows]

            paginated_query = query
            query_params = dict(params)

            if cursor is not None:
                order_by_field = order_by.split()[0]
                is_descending = "DESC" in order_by.upper()
                cursor_operator = "<" if is_descending else ">"

                has_where = "WHERE" in query.upper()
                connector = "AND" if has_where else "WHERE"

                paginated_query += f" {connector} {order_by_field} {cursor_operator} :cursor_val"
                query_params["cursor_val"] = cursor

            if "ORDER BY" not in paginated_query.upper():
                paginated_query += f" ORDER BY {order_by}"

            paginated_query += f" LIMIT {size + 1}"

            result = self.db.execute(text(paginated_query), query_params)
            rows = result.fetchall()
            results = [dict(row._mapping) for row in rows]

            has_more = len(results) > size
            if has_more:
                results.pop()

            next_cursor = None
            if results:
                last_row = results[-1]
                field_name = cursor_field.split(".")[-1] if "." in cursor_field else cursor_field
                next_cursor = last_row.get(field_name)

            return {
                "data": results,
                "pagination": {
                    "has_more": has_more,
                    "next_cursor": next_cursor if has_more else None,
                    "size": size
                }
            }
        except Exception as e:
            raise Exception(f"Custom query execution failed: {str(e)}")

    def insert_raw(
        self,
        table_name: str,
        data: Dict[str, Any],
        returning: Union[str, List[str]] = "*"
    ) -> Dict[str, Any]:
        """Insert without commit — use inside transaction() only."""
        columns = list(data.keys())
        placeholders = ", ".join([f":p{i}" for i in range(len(columns))])
        column_names = ", ".join(columns)
        returning_clause = ", ".join(returning) if isinstance(returning, list) else returning

        query = f"""
            INSERT INTO {table_name} ({column_names})
            VALUES ({placeholders})
            RETURNING {returning_clause}
        """
        params = {f"p{i}": v for i, v in enumerate(data.values())}
        result = self.db.execute(text(query), params)
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def update_raw(
        self,
        table_name: str,
        data: Dict[str, Any],
        conditions: Dict[str, Any],
    ) -> None:
        """Update without commit — use inside transaction() only."""
        set_parts = [f"{col} = :set_{i}" for i, col in enumerate(data.keys())]
        params = {f"set_{i}": v for i, v in enumerate(data.values())}
        where_clause, where_params = self._build_where_clause(conditions, start_index=len(data))
        params.update(where_params)
        query = f"UPDATE {table_name} SET {', '.join(set_parts)} WHERE {where_clause}"
        self.db.execute(text(query), params)

    def transaction(self, callback):
        try:
            result = callback(self)
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Transaction failed: {str(e)}")

    def _build_where_clause(
        self,
        conditions: Dict[str, Any],
        start_index: int = 0,
        condition_type: str = "AND"
    ) -> tuple:
        keys = list(conditions.keys())

        if not keys:
            return "", {}

        clauses = []
        params = {}
        value_index = start_index

        for key in keys:
            value = conditions[key]
            param_name = f"w_{value_index}"

            if value is None:
                clauses.append(f"{key} IS NULL")
            elif isinstance(value, list):
                in_params = []
                for i, v in enumerate(value):
                    in_param = f"{param_name}_{i}"
                    params[in_param] = v
                    in_params.append(f":{in_param}")
                clauses.append(f"{key} IN ({', '.join(in_params)})")
            elif isinstance(value, dict) and "operator" in value:
                operator = value["operator"].upper()
                val = value["value"]

                if operator in ["IN", "NOT IN"] and isinstance(val, list):
                    in_params = []
                    for i, v in enumerate(val):
                        in_param = f"{param_name}_{i}"
                        params[in_param] = v
                        in_params.append(f":{in_param}")
                    clauses.append(f"{key} {operator} ({', '.join(in_params)})")
                else:
                    params[param_name] = val
                    clauses.append(f"{key} {value['operator']} :{param_name}")
            else:
                params[param_name] = value
                clauses.append(f"{key} = :{param_name}")

            value_index += 1

        join_operator = " OR " if condition_type == "OR" else " AND "

        return join_operator.join(clauses), params

def get_crud(db: Session) -> DatabaseCRUD:
    return DatabaseCRUD(db)