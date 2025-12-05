import sqlite3
from typing import Dict, Any, List
from database_helper import PokemonDatabase


class PopularityLearner:
    def __init__(self, db: PokemonDatabase):
        self.db = db
        self.learning_rate = 0.1  # learning rate for popularity updates
        self.decay_rate = 0.995   # decay factor for non-candidate Pokemon popularity
        
    def update_popularity(self, target_pokemon_id: int, 
                         candidates: List[Dict[str, Any]], 
                         was_correct: bool):
        candidate_ids = [p['ID'] for p in candidates]
        
        # update the target/correct pokemon (positive reward)
        self._adjust_popularity(target_pokemon_id, reward=1.0)
        
        # updating other candidates (negative reward)
        for candidate in candidates:
            if candidate['ID'] != target_pokemon_id:
                self._adjust_popularity(candidate['ID'], reward=-0.2)
        
        # apply decay to non-candidate Pokemon (prevents runaway popularity)
        self._apply_decay(exclude_ids=[target_pokemon_id] + candidate_ids)
        
    def _adjust_popularity(self, pokemon_id: int, reward: float):
        # get current popularity
        self.db.cursor.execute("SELECT Popularity FROM mytable WHERE ID = ?", (pokemon_id,))
        result = self.db.cursor.fetchone()
        
        if result is None:
            return
        
        current_popularity = result[0] if result[0] is not None else 0
        
        # update using learning rate
        new_popularity = current_popularity + (self.learning_rate * reward)
        
        # clamp to reasonable range (0 to 100)
        new_popularity = max(0, min(100, new_popularity))
        
        # update database
        self.db.cursor.execute(
            "UPDATE mytable SET Popularity = ? WHERE ID = ?",
            (new_popularity, pokemon_id)
        )
        self.db.connection.commit()
        
    def _apply_decay(self, exclude_ids: List[int]):
        # decay popularity of all Pokemon not in exclude_ids
        # only apply if there are IDs to exclude
        if len(exclude_ids) > 0:
            placeholders = ','.join('?' * len(exclude_ids))
            self.db.cursor.execute(
                f"UPDATE mytable SET Popularity = Popularity * ? WHERE ID NOT IN ({placeholders})",
                [self.decay_rate] + exclude_ids
            )
            self.db.connection.commit()
    
    def get_most_popular(self, candidates: List[Dict[str, Any]], top_n: int = 1) -> List[Dict[str, Any]]:
        # return the top N most popular Pokemon from the candidates
        # sort by popularity (highest first), then by ID for consistency
        sorted_candidates = sorted(
            candidates, 
            key=lambda p: (p.get('Popularity', 0), -p['ID']),
            reverse=True
        )
        
        return sorted_candidates[:top_n]
    
    def get_popularity_stats(self) -> Dict[str, Any]:
        self.db.cursor.execute("""
            SELECT 
                MIN(Popularity) as min_pop,
                MAX(Popularity) as max_pop,
                AVG(Popularity) as avg_pop,
                COUNT(*) as total
            FROM mytable
        """)
        
        stats = dict(self.db.cursor.fetchone())
        
        # top 10 popular Pokemon
        self.db.cursor.execute("""
            SELECT Name, Popularity 
            FROM mytable 
            ORDER BY Popularity DESC, ID ASC
            LIMIT 10
        """)
        
        stats['top_pokemon'] = [
            {'name': row[0], 'popularity': row[1]} 
            for row in self.db.cursor.fetchall()
        ]
        
        return stats
    
    def reset_all_popularity(self):
        self.db.cursor.execute("UPDATE mytable SET Popularity = 0")
        self.db.connection.commit()


class AdaptiveQuestionSelector:
    def __init__(self):
        # initialize selector
        self.question_effectiveness = {}  # track question effectiveness stats
        
    def record_question_result(self, question_type: str, question_detail: Any,
                               before_count: int, after_count: int):
        key = f"{question_type}:{question_detail}"
        
        # calculate reduction ratio
        if before_count > 0:
            reduction_ratio = (before_count - after_count) / before_count
        else:
            reduction_ratio = 0
        
        # update running average
        if key not in self.question_effectiveness:
            self.question_effectiveness[key] = {
                'total_reduction': reduction_ratio,
                'count': 1,
                'avg_reduction': reduction_ratio
            }
        else:
            stats = self.question_effectiveness[key]
            stats['total_reduction'] += reduction_ratio
            stats['count'] += 1
            stats['avg_reduction'] = stats['total_reduction'] / stats['count']
    
    def get_question_boost(self, question_type: str, question_detail: Any) -> float:
        key = f"{question_type}:{question_detail}"
        
        if key in self.question_effectiveness:
            # return small boost based on average effectiveness
            avg_reduction = self.question_effectiveness[key]['avg_reduction']
            return avg_reduction * 0.3  # max boost
        
        return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        if not self.question_effectiveness:
            return {'total_questions_tracked': 0, 'top_questions': []}
        
        # sort by effectiveness
        sorted_questions = sorted(
            self.question_effectiveness.items(),
            key=lambda x: x[1]['avg_reduction'],
            reverse=True
        )
        
        return {
            'total_questions_tracked': len(self.question_effectiveness),
            'top_questions': [
                {
                    'question': key,
                    'avg_reduction': stats['avg_reduction'],
                    'times_used': stats['count']
                }
                for key, stats in sorted_questions[:10]
            ]
        }

