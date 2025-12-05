import sqlite3
from typing import List, Dict, Any, Optional


class PokemonDatabase:
    def __init__(self, db_path: str = "database_files/database/pokemon_database.db"):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.connect()
        
    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row  # access columns by name
        self.cursor = self.connection.cursor()
        
    def close(self):
        if self.connection:
            self.connection.close()
            
    def get_all_pokemon(self) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM mytable")
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_pokemon_count(self) -> int:
        self.cursor.execute("SELECT COUNT(*) as count FROM mytable")
        return self.cursor.fetchone()['count']
    
    def get_pokemon_by_id(self, pokemon_id: int) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM mytable WHERE ID = ?", (pokemon_id,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def get_pokemon_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        self.cursor.execute("SELECT * FROM mytable WHERE Name = ?", (name,))
        row = self.cursor.fetchone()
        return dict(row) if row else None
    
    def filter_pokemon(self, attribute: str, value: Any) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM mytable WHERE {attribute} = ?"
        self.cursor.execute(query, (value,))
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_distinct_values(self, attribute: str) -> List[Any]:
        query = f"SELECT DISTINCT {attribute} FROM mytable WHERE {attribute} IS NOT NULL ORDER BY {attribute}"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]
    
    def count_by_attribute(self, attribute: str, value: Any) -> int:
        query = f"SELECT COUNT(*) as count FROM mytable WHERE {attribute} = ?"
        self.cursor.execute(query, (value,))
        return self.cursor.fetchone()['count']
    
    def filter_pokemon_multi(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not filters:
            return self.get_all_pokemon()
        
        conditions = []
        values = []
        
        for attr, value in filters.items():
            conditions.append(f"{attr} = ?")
            values.append(value)
        
        query = f"SELECT * FROM mytable WHERE {' AND '.join(conditions)}"
        self.cursor.execute(query, values)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_attribute_distribution(self, attribute: str, current_filters: Dict[str, Any] = None) -> Dict[Any, int]:
        if current_filters:
            conditions = []
            values = []
            for attr, value in current_filters.items():
                conditions.append(f"{attr} = ?")
                values.append(value)
            
            where_clause = " WHERE " + " AND ".join(conditions)
            query = f"SELECT {attribute}, COUNT(*) as count FROM mytable{where_clause} GROUP BY {attribute}"
            self.cursor.execute(query, values)
        else:
            query = f"SELECT {attribute}, COUNT(*) as count FROM mytable GROUP BY {attribute}"
            self.cursor.execute(query)
        
        return {row[0]: row[1] for row in self.cursor.fetchall()}
    
    def get_queryable_attributes(self) -> List[str]:
        # only return boolean/binary attributes for yes/no questions
        return [
            'Lengendary', 'Mythical', 'Baby', 'Fossile', 'Starter',
            'Mega_Evolve', 'Gigantamax', 'Evolves', 'Evolves_from_stone',
            'Evolves_from_trading'
        ]
    
    def get_all_types(self) -> List[str]:
        types = set()
        self.cursor.execute("SELECT DISTINCT Type_1 FROM mytable WHERE Type_1 IS NOT NULL")
        types.update([row[0] for row in self.cursor.fetchall()])
        self.cursor.execute("SELECT DISTINCT Type_2 FROM mytable WHERE Type_2 IS NOT NULL")
        types.update([row[0] for row in self.cursor.fetchall()])
        return sorted(list(types))
    
    def get_all_colors(self) -> List[str]:
        return self.get_distinct_values('Primay_Color')
    
    def get_all_regions(self) -> List[str]:
        return self.get_distinct_values('Region')
    
    def get_all_generations(self) -> List[int]:
        return self.get_distinct_values('Generation')
    
    def has_type(self, pokemon_filters: Dict[str, Any], type_name: str) -> int:
        conditions = []
        values = []
        
        for attr, value in pokemon_filters.items():
            conditions.append(f"{attr} = ?")
            values.append(value)
        
        type_condition = "(Type_1 = ? OR Type_2 = ?)"
        values.extend([type_name, type_name])
        
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions) + f" AND {type_condition}"
        else:
            where_clause = f" WHERE {type_condition}"
        
        query = f"SELECT COUNT(*) as count FROM mytable{where_clause}"
        self.cursor.execute(query, values)
        return self.cursor.fetchone()['count']

