import random
from typing import Dict, Any
from database_helper import PokemonDatabase
from game_ai import TwentyQuestionsAI
from learning import PopularityLearner


class TwentyQuestionsGame: 
    def __init__(self):
        self.db = PokemonDatabase()
        self.ai = TwentyQuestionsAI(self.db, use_learning=True)
        self.learner = PopularityLearner(self.db)
        
    def start(self):
        print("=" * 60)
        print("        POKEMON 20 QUESTIONS GAME")
        print("=" * 60)
        print(f"\nThink of any Pokemon from the database ({self.db.get_pokemon_count()} total).")
        print("I will try to guess it by asking yes/no questions.\n")
        print("Type 'stats' to see learning statistics, or press Enter to play...")
        
        choice = input().strip().lower()
        
        if choice == 'stats':
            self.show_stats()
            input("\nPress Enter to start playing...")
        
        self.play_game()
    
    def play_game(self):
        self.ai.reset()
        
        while self.ai.questions_asked < self.ai.max_questions:
            remaining = self.ai.get_remaining_count()
            
            print(f"\n{'=' * 60}")
            print(f"Question {self.ai.questions_asked + 1} of {self.ai.max_questions}")
            print(f"Remaining possibilities: {remaining}")
            print('=' * 60)
            
            # Check if we should guess
            if remaining <= 1:
                self.make_final_guess()
                break
            
            # Try to guess if 3 or fewer candidates remain
            if remaining <= 3:
                print(f"\nI'm ready to guess! Remaining candidates: {', '.join([p['Name'] for p in self.ai.get_top_candidates()])}")
                
                if self.attempt_guess():
                    # Guess was correct, end the game
                    self.play_again()
                    return
                else:
                    # Guess was wrong, re-check remaining count
                    print("\nOkay, let me try again...")
                    # Continue to next iteration to check if we can guess again or need to ask
                    continue
            elif remaining <= 5:
                print(f"\nNarrowing down candidates: {', '.join([p['Name'] for p in self.ai.get_top_candidates(5)])}")
            
            question_type, question_detail = self.ai.ask_question()
            
            if question_type is None:
                print("\nI've run out of distinguishing questions!")
                self.make_final_guess()
                break
            
            question = self.ai.format_question(question_type, question_detail)
            print(f"\n{question}")
            
            # get answer
            while True:
                answer = input("Your answer (yes/no): ").strip().lower()
                if answer in ['yes', 'y', 'no', 'n']:
                    answer_bool = answer in ['yes', 'y']
                    break
                print("Please answer 'yes' or 'no'")
            
            self.ai.update_filters(question_type, question_detail, answer_bool)
            
            # progress
            new_remaining = self.ai.get_remaining_count()
            reduction = remaining - new_remaining
            print(f"Eliminated {reduction} possibilities")
        
        if self.ai.questions_asked >= self.ai.max_questions:
            print(f"\nI've used all {self.ai.max_questions} questions!")
            self.make_final_guess()
        
        self.play_again()
    
    def attempt_guess(self) -> bool:
        # attempt guess function
        candidates = self.ai.get_top_candidates(3)
        
        if not candidates:
            return False
        
        # Make a guess with the most popular candidate
        guess = candidates[0]
        print(f"\nIs it {guess['Name']}?")
        
        confirm = input("(yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            print(f"\nYay! I guessed {guess['Name']} correctly in {self.ai.questions_asked} questions!")
            self._show_pokemon_details(guess)
            # Update learning: reward correct guess
            self.learner.update_popularity(guess['ID'], candidates, was_correct=True)
            return True
        else:
            print(f"Not {guess['Name']}.")
            # Remove the wrong guess from candidates
            self.ai.remaining_pokemon = [p for p in self.ai.remaining_pokemon if p['ID'] != guess['ID']]
            return False
    
    def make_final_guess(self):
        # final guess
        candidates = self.ai.get_top_candidates(10)
        
        if len(candidates) == 1:
            guess = candidates[0]
            print(f"\nI've got it! Is it {guess['Name']}?")
        elif len(candidates) == 0:
            print(f"\nI couldn't narrow it down - no Pokemon match the criteria!")
            confirm = input("\nWhat Pokemon were you thinking of? ").strip().title()
            actual_pokemon = self.db.get_pokemon_by_name(confirm)
            if actual_pokemon:
                print(f"\nFound {confirm}! Let me see its details...")
                self._show_pokemon_details(actual_pokemon)
            self.play_again()
            return
        else:
            print(f"\nI have {len(candidates)} possible Pokemon left.")
            if len(candidates) <= 10:
                print("\nRemaining candidates:")
                for i, pokemon in enumerate(candidates, 1):
                    print(f"  {i}. {pokemon['Name']}")
            
            guess = candidates[0]
            print(f"\nMy best guess is: {guess['Name']}")
        
        confirm = input("\nAm I correct? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            print(f"\nYay! I guessed {guess['Name']} correctly in {self.ai.questions_asked} questions!")
            self._show_pokemon_details(guess)
            # Update learning: reward correct guess
            self.learner.update_popularity(guess['ID'], candidates, was_correct=True)
        else:
            print(f"\nOh no! I was wrong.")
            actual = input("What Pokemon were you thinking of? ").strip().title()
            actual_pokemon = self.db.get_pokemon_by_name(actual)
            if actual_pokemon:
                print(f"\nAh, {actual}! Let me see its details...")
                self._show_pokemon_details(actual_pokemon)
                print(f"\nI'll learn from this for next time!")
                # Update learning: learn from mistake
                self.learner.update_popularity(actual_pokemon['ID'], candidates, was_correct=False)
            else:
                print(f"\nI couldn't find '{actual}' in the database.")
    
    def _show_pokemon_details(self, pokemon: Dict[str, Any]):
        """Display detailed information about a Pokemon."""
        print(f"\n{'-' * 60}")
        print(f"  {pokemon['Name'].upper()}")
        print('-' * 60)
        print(f"Type: {pokemon['Type_1']}" + (f"/{pokemon['Type_2']}" if pokemon['Type_2'] else ""))
        print(f"Color: {pokemon['Primay_Color']}")
        print(f"Region: {pokemon['Region']}")
        print(f"Generation: {pokemon['Generation']}")
        
        special = []
        if pokemon['Lengendary'] == 'true':
            special.append('Legendary')
        if pokemon['Mythical'] == 'true':
            special.append('Mythical')
        if pokemon['Starter'] == 'true':
            special.append('Starter')
        if pokemon['Baby'] == 'true':
            special.append('Baby')
        if pokemon['Fossile'] == 'true':
            special.append('Fossil')
        if pokemon['Mega_Evolve'] == 'true':
            special.append('Mega Evolution')
        if pokemon['Gigantamax'] == 'true':
            special.append('Gigantamax')
        
        if special:
            print(f"Special: {', '.join(special)}")
        print('-' * 60)
    
    def show_stats(self):
        print("\n" + "=" * 60)
        print("LEARNING STATISTICS")
        print("=" * 60)
        
        stats = self.learner.get_popularity_stats()
        
        print(f"\nPopularity Distribution:")
        print(f"  Minimum: {stats['min_pop']:.2f}")
        print(f"  Maximum: {stats['max_pop']:.2f}")
        print(f"  Average: {stats['avg_pop']:.2f}")
        
        print(f"\nTop 10 Most Popular Pokemon (based on gameplay):")
        for i, pokemon in enumerate(stats['top_pokemon'], 1):
            print(f"  {i:2d}. {pokemon['name']:15s} - Popularity: {pokemon['popularity']:.2f}")
        
        print("\n" + "=" * 60)
    
    def play_again(self):
        # play again?
        print("\n" + "=" * 60)
        play_again = input("\nPlay again? (yes/no): ").strip().lower()
        
        if play_again in ['yes', 'y']:
            print("\n")
            self.start()
        else:
            print("\nThanks for playing!")
            self.db.close()


def main():
    game = TwentyQuestionsGame()
    try:
        game.start()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")
        game.db.close()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        game.db.close()


if __name__ == "__main__":
    main()
def main():
    game = TwentyQuestionsGame()
    try:
        game.start()
    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")
        game.db.close()
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        game.db.close()


if __name__ == "__main__":
    main()
