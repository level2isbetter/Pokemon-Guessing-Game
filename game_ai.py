import math
from typing import List, Dict, Any, Tuple
from database_helper import PokemonDatabase


class TwentyQuestionsAI:
    def __init__(self, db: PokemonDatabase, use_learning: bool = True):
        self.db = db
        self.current_filters = {}
        self.remaining_pokemon = db.get_all_pokemon()
        self.questions_asked = 0
        self.max_questions = 20
        self.question_history = []
        self.asked_types = set()
        self.asked_colors = set()
        self.asked_regions = set()
        self.asked_generations = set()
        self.use_learning = use_learning
        
    def reset(self):
        self.current_filters = {}
        self.remaining_pokemon = self.db.get_all_pokemon()
        self.questions_asked = 0
        self.question_history = []
        self.asked_types = set()
        self.asked_colors = set()
        self.asked_regions = set()
        self.asked_generations = set()
        
    def calculate_entropy(self, distribution: Dict[Any, int]) -> float:
        total = sum(distribution.values())
        if total == 0:
            return 0.0
        
        entropy = 0.0
        for count in distribution.values():
            if count > 0:
                probability = count / total
                entropy -= probability * math.log2(probability)
        
        return entropy
    
    def calculate_information_gain_for_type(self, type_name: str) -> float:
        # calculate information gain for asking about a specific type
        if not self.remaining_pokemon:
            return 0.0
        
        current_entropy = math.log2(len(self.remaining_pokemon))
        
        # count how many have this type vs don't
        has_type_count = sum(1 for p in self.remaining_pokemon 
                            if p['Type_1'] == type_name or p['Type_2'] == type_name)
        doesnt_have_count = len(self.remaining_pokemon) - has_type_count
        
        if has_type_count == 0 or doesnt_have_count == 0:
            return 0.0
        
        # calculate weighted entropy
        total = len(self.remaining_pokemon)
        prob_has = has_type_count / total
        prob_doesnt = doesnt_have_count / total
        
        entropy_has = math.log2(has_type_count) if has_type_count > 1 else 0
        entropy_doesnt = math.log2(doesnt_have_count) if doesnt_have_count > 1 else 0
        
        weighted_entropy = prob_has * entropy_has + prob_doesnt * entropy_doesnt
        
        return current_entropy - weighted_entropy
    
    def calculate_information_gain_for_value(self, attribute: str, value: Any) -> float:
        if not self.remaining_pokemon:
            return 0.0
        
        current_entropy = math.log2(len(self.remaining_pokemon))
        
        # count how many have this value vs don't
        has_value_count = sum(1 for p in self.remaining_pokemon if p[attribute] == value)
        doesnt_have_count = len(self.remaining_pokemon) - has_value_count
        
        if has_value_count == 0 or doesnt_have_count == 0:
            return 0.0
        
        # calculate weighted entropy
        total = len(self.remaining_pokemon)
        prob_has = has_value_count / total
        prob_doesnt = doesnt_have_count / total
        
        entropy_has = math.log2(has_value_count) if has_value_count > 1 else 0
        entropy_doesnt = math.log2(doesnt_have_count) if doesnt_have_count > 1 else 0
        
        weighted_entropy = prob_has * entropy_has + prob_doesnt * entropy_doesnt
        
        return current_entropy - weighted_entropy
    
    def calculate_information_gain(self, attribute: str) -> float:
        # get distribution of this attribute in remaining Pokemon
        distribution = self.db.get_attribute_distribution(attribute, self.current_filters)
        
        if not distribution or len(distribution) == 1:
            return 0.0
        
        # current entropy
        current_entropy = math.log2(len(self.remaining_pokemon)) if self.remaining_pokemon else 0
        
        # calculate weighted average entropy after asking about this attribute
        total = sum(distribution.values())
        weighted_entropy = 0.0
        
        for value, count in distribution.items():
            if count > 0:
                probability = count / total
                # entropy of this subset
                subset_entropy = math.log2(count) if count > 1 else 0
                weighted_entropy += probability * subset_entropy
        
        return current_entropy - weighted_entropy
    
    def find_best_question(self) -> Tuple[str, Any]:
        if not self.remaining_pokemon:
            return None, None
        
        best_question = None
        best_gain = -1.0
        
        # check boolean attributes
        queryable_attributes = self.db.get_queryable_attributes()
        available_attributes = [
            attr for attr in queryable_attributes 
            if attr not in self.current_filters
        ]
        
        for attribute in available_attributes:
            gain = self.calculate_information_gain(attribute)
            if gain > best_gain:
                best_gain = gain
                best_question = ('attribute', attribute)
        
        # check types (not yet asked about)
        all_types = self.db.get_all_types()
        available_types = [t for t in all_types if t not in self.asked_types]
        for type_name in available_types:
            gain = self.calculate_information_gain_for_type(type_name)
            if gain > best_gain:
                best_gain = gain
                best_question = ('type', type_name)
        
        # check colors
        all_colors = self.db.get_all_colors()
        available_colors = [c for c in all_colors if c not in self.asked_colors]
        for color in available_colors:
            gain = self.calculate_information_gain_for_value('Primay_Color', color)
            if gain > best_gain:
                best_gain = gain
                best_question = ('color', color)
        
        # check regions
        all_regions = self.db.get_all_regions()
        available_regions = [r for r in all_regions if r not in self.asked_regions]
        for region in available_regions:
            gain = self.calculate_information_gain_for_value('Region', region)
            if gain > best_gain:
                best_gain = gain
                best_question = ('region', region)
        
        # check generations
        all_generations = self.db.get_all_generations()
        available_generations = [g for g in all_generations if g not in self.asked_generations]
        for generation in available_generations:
            gain = self.calculate_information_gain_for_value('Generation', generation)
            if gain > best_gain:
                best_gain = gain
                best_question = ('generation', generation)
        
        return best_question if best_question else (None, None)
    
    def ask_question(self) -> Tuple[str, Any]:
        # generate the next optimal yes/no question
        return self.find_best_question()
    
    def update_filters(self, question_type: str, question_detail: Any, answer: bool):
        # update current filters and remaining Pokemon based on the answer
        if question_type == 'attribute':
            # boolean attribute - filter remaining Pokemon
            value = 'true' if answer else 'false'
            self.current_filters[question_detail] = value
            # filter the already-narrowed list, not the whole database
            self.remaining_pokemon = [p for p in self.remaining_pokemon if p[question_detail] == value]
            
        elif question_type == 'type':
            # filter by type
            if answer:
                # keep Pokemon that have this type
                self.remaining_pokemon = [p for p in self.remaining_pokemon 
                                         if p['Type_1'] == question_detail or p['Type_2'] == question_detail]
            else:
                # remove Pokemon that have this type
                self.remaining_pokemon = [p for p in self.remaining_pokemon 
                                         if p['Type_1'] != question_detail and p['Type_2'] != question_detail]
            self.asked_types.add(question_detail)
            
        elif question_type == 'color':
            if answer:
                self.remaining_pokemon = [p for p in self.remaining_pokemon if p['Primay_Color'] == question_detail]
            else:
                self.remaining_pokemon = [p for p in self.remaining_pokemon if p['Primay_Color'] != question_detail]
            self.asked_colors.add(question_detail)
            
        elif question_type == 'region':
            if answer:
                self.remaining_pokemon = [p for p in self.remaining_pokemon if p['Region'] == question_detail]
            else:
                self.remaining_pokemon = [p for p in self.remaining_pokemon if p['Region'] != question_detail]
            self.asked_regions.add(question_detail)
            
        elif question_type == 'generation':
            if answer:
                self.remaining_pokemon = [p for p in self.remaining_pokemon if p['Generation'] == question_detail]
            else:
                self.remaining_pokemon = [p for p in self.remaining_pokemon if p['Generation'] != question_detail]
            self.asked_generations.add(question_detail)
        
        self.questions_asked += 1
        self.question_history.append((question_type, question_detail, answer))
        
    def get_remaining_count(self) -> int:
        return len(self.remaining_pokemon)
    
    def make_guess(self) -> Dict[str, Any]:
        # make a guess based on the most likely remaining Pokemon
        if self.remaining_pokemon:
            return self.remaining_pokemon[0]
        return None
    
    def get_top_candidates(self, n: int = 5) -> List[Dict[str, Any]]:
        # get the top N most likely remaining Pokemon
        if self.use_learning:
            # sort by popularity (highest first), then by ID for tie-breaking
            sorted_pokemon = sorted(
                self.remaining_pokemon,
                key=lambda p: (p.get('Popularity', 0), -p['ID']),
                reverse=True
            )
            return sorted_pokemon[:n]
        else:
            return self.remaining_pokemon[:n]
    
    def format_question(self, question_type: str, question_detail: Any) -> str:
        # yes/no question formatting
        if question_type == 'attribute':
            question_templates = {
                'Lengendary': "Is it a legendary Pokemon?",
                'Mythical': "Is it a mythical Pokemon?",
                'Baby': "Is it a baby Pokemon?",
                'Fossile': "Is it a fossil Pokemon?",
                'Starter': "Is it a starter Pokemon?",
                'Mega_Evolve': "Can it mega evolve?",
                'Gigantamax': "Can it Gigantamax?",
                'Evolves': "Does it evolve into another Pokemon?",
                'Evolves_from_stone': "Does it evolve using a stone?",
                'Evolves_from_trading': "Does it evolve through trading?"
            }
            return question_templates.get(question_detail, f"Is the {question_detail} true?")
        
        elif question_type == 'type':
            return f"Is it a {question_detail}-type Pokemon?"
        
        elif question_type == 'color':
            return f"Is it {question_detail} in color?"
        
        elif question_type == 'region':
            return f"Is it from the {question_detail} region?"
        
        elif question_type == 'generation':
            return f"Is it from Generation {question_detail}?"
        
        return "Unknown question"

