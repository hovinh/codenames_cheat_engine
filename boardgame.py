import questionary
from nltk.corpus import wordnet as wn
from spymaster import SpyMaster
import os

class CodenamesBoardGame(object):
    def __init__(self, keyword_list, team_guessword_dict):
        '''
        @params:
            - keyword_list: list of str, 25 code words picked.
            - team_guessword_dict: dictionary of list of str. Example:
                {
                    'team_blue': ['house', 'bird', 'book', ...], # 8 words, always play first
                    'team_red': ['cat', 'dog', 'pineapple', ...], # 7 words
                }
        '''

        is_valid, invalid_word_list = self.check_all_keywords_valid(keyword_list)
        if (is_valid == False):
            raise ValueError(f'Word(s) cannot be found in WordNet: {invalid_word_list}')

        self._keyword_list = keyword_list
        self._team_guessword_dict = team_guessword_dict
        self._team_name_list = ['team_blue', 'team_red']
        self._team_winning_score_list = [9, 8]
        self._team_score_dict = {
            'team_blue': 0,
            'team_red': 0,
        }
        self._team_turn = 0
        self._game_history = ''

        # SpyMaster can be shared among 2 teams because the behaviour is deterministic
        self._spy_master = SpyMaster()

        # keep track of all the words have been chosen so far
        self._chosenword_list = list()

    def check_all_keywords_valid(self, keyword_list):
        is_valid = True
        invalid_word_list = []
        for word in keyword_list:
            # the word must exist in WordNet
            synset_list = wn.synsets(word)
            is_existed = len(synset_list) > 0
            if (is_existed == False):
                invalid_word_list.append(word)
                is_valid = False

        return is_valid, invalid_word_list

    def start_game(self):

        while (self.check_game_is_over() == False):
            team_name = self.get_team_turn()
            keyword_list, guessword_list, chosenword_list = self.get_keyword_guessword_chosenword_list(team_name)
            
            self.print_and_update_game_history(f"This is {team_name}'s turn.")
            hint_list, filtered_guessword_list = self._spy_master.suggest(keyword_list=keyword_list, 
                                                                          guessword_list=guessword_list, 
                                                                          chosenword_list=chosenword_list)
            selected_hint, selected_words = self.select_hint_and_guesswords(hint_list, filtered_guessword_list)
            self.print_and_update_game_history(f"Selected hint: {selected_hint} | Selected guessed words: {selected_words}")
            
            self.update_chosenword_list(new_chosenword_list=selected_words)
            score, required_score = self.update_team_score(team_name)
            self.print_and_update_game_history(f'Updated score: {score}/{required_score}')
            self.switch_turn()

        return self._game_history

    def check_game_is_over(self):
        for team_name, winning_score in zip(self._team_name_list, self._team_winning_score_list):
            team_score = self._team_score_dict[team_name]
            if (team_score >= winning_score):
                print (f'The winner is {team_name}!!!')
                return True

        return False       

    def select_hint_and_guesswords(self, hint_list, guessword_list, do_clear_screen=True):
        #hint_str_list = [f'Synset {ss} | Definition: {defi}\n' + (len(examples)>0)*f'Examples: {examples}\n' + f'Count: {count} | Lemmas: {lemma} | Connected words: {corr_words}' for ss, defi, examples, lemma, count, corr_words in hint_list]
        
        selected_idx = 0
        numb_candidates_shown = 8
        numb_candidates_total = len(hint_list)

        # If there is hint can lead to 2 words at least
        if (numb_candidates_total > 0):
            if (do_clear_screen == True):
                self.clear_screen()

            while (True):
                if (do_clear_screen == True):
                    self.clear_screen()

                selected_idx_max = min(selected_idx+numb_candidates_shown, numb_candidates_total)
                candidate_idx_list = [i for i in range(selected_idx, selected_idx_max, 1)]
                #print (f'Selected: {selected_idx, selected_idx_max} | Candidated: {candidate_idx_list}')
                next_idx = candidate_idx_list[-1] + 1
                #print (f'Next idx: {next_idx}')
            
                for idx in candidate_idx_list:
                    hint_str = str(hint_list[idx])
                    print (f'<{idx}> ', hint_str, '\n')

                numb_candidates_remaining = numb_candidates_total - selected_idx_max
                numb_candidates_shown_next = min(numb_candidates_shown, numb_candidates_remaining)
                if (numb_candidates_shown_next > 0):
                    print (f'<{next_idx}> See the next {numb_candidates_shown_next} synsets out of {numb_candidates_total}.')
                else:
                    print (f'<{next_idx}> Back to the beginning.')
        
                selected_idx_str = questionary.select(
                    'Select hint',
                    choices = [str(i) for i in candidate_idx_list] + [str(next_idx)]
                ).ask()

                selected_idx = int(selected_idx_str)
                if (selected_idx in candidate_idx_list):
                    break
                else:
                    if (next_idx < numb_candidates_total):
                        selected_idx = next_idx
                    else:
                        selected_idx = 0
            
            selected_hint = hint_list[selected_idx]
            synset, valid_word_count, corr_words = selected_hint.get_info()

            selected_words = questionary.checkbox(
                'Select one or more guessed words',
                choices = corr_words
            ).ask()

        # Else we just list of individual guess words and pick one
        else:
            if (do_clear_screen == True):
                self.clear_screen()

            numb_guesswords = len(guessword_list)
            print ('There is no hint covering at least 2 words.')
            for idx, word in enumerate(guessword_list):
                ss_list = wn.synsets(word)
                print (f'<{idx}> ', word, f' | Synsets: {ss_list}\n')

            selected_idx_str = questionary.select(
                'Select hint',
                choices = [str(i) for i in range(numb_guesswords)]
            ).ask()

            selected_idx = int(selected_idx_str)
            word = guessword_list[selected_idx]
            synset = wn.synsets(word)[0]
            selected_words = [word]

        return synset, selected_words

    def update_team_score(self, team_name):
        guessword_list = self._team_guessword_dict[team_name]
        chosenword_list = self._chosenword_list
        score = 0
        for word in guessword_list:
            if word in chosenword_list:
                score += 1
        
        self._team_score_dict[team_name] = score
        required_score = self._team_winning_score_list[self._team_turn]
        return score, required_score

    def get_keyword_guessword_chosenword_list(self, team_name):
        keyword_list = self._keyword_list
        guessword_list = self._team_guessword_dict[team_name]
        chosenword_list = self._chosenword_list

        return keyword_list, guessword_list, chosenword_list

    def get_team_turn(self):
        return self._team_name_list[self._team_turn]

    def switch_turn(self):
        self._team_turn = 1-self._team_turn

    def update_chosenword_list(self, new_chosenword_list):
        self._chosenword_list.extend(new_chosenword_list)

    def update_game_history(self, text):
        self._game_history += f'{text}\n'

    def print_and_update_game_history(self, text):
        print (text)
        self.update_game_history(text)

    def clear_screen(self):
        # Source: https://www.geeksforgeeks.org/clear-screen-python/
        # for windows 
        if (os.name == 'nt'): 
            _ = os.system('cls') 
    
        # for mac and linux(here, os.name is 'posix') 
        else: 
            _ = os.system('clear') 