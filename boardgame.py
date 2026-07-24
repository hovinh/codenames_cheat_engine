from nltk.corpus import wordnet as wn
from spymaster import SpyMaster


class CodenamesBoardGame(object):
    def __init__(self, keyword_list, team_guessword_dict, spy_master=None):
        '''
        @params:
            - keyword_list: list of str, code words on the board.
            - team_guessword_dict: dictionary of list of str. Example:
                {
                    'team_blue': ['house', 'bird', 'book', ...], # always plays first
                    'team_red': ['cat', 'dog', 'pineapple', ...],
                }
            - spy_master: optional clue-generation engine implementing
              suggest(keyword_list, guessword_list, chosenword_list). Defaults
              to the WordNet-based SpyMaster; pass e.g. a ConceptNetSpyMaster
              to swap engines.
        '''

        is_valid, invalid_word_list = self.check_all_keywords_valid(keyword_list)
        if (is_valid == False):
            raise ValueError(f'Word(s) cannot be found in WordNet: {invalid_word_list}')

        self._keyword_list = keyword_list
        self._team_guessword_dict = team_guessword_dict
        self._team_name_list = ['team_blue', 'team_red']
        # a team wins once every one of its own words has been found
        self._team_winning_score_list = [
            len(team_guessword_dict['team_blue']),
            len(team_guessword_dict['team_red']),
        ]
        self._team_score_dict = {
            'team_blue': 0,
            'team_red': 0,
        }
        self._team_turn = 0

        # list of dict entries: {'team', 'hint', 'selected_words', 'score', 'required_score'}
        self._game_history = []

        # SpyMaster can be shared among 2 teams because the behaviour is deterministic
        self._spy_master = spy_master if spy_master is not None else SpyMaster()

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

    def get_suggestions(self):
        '''Return (hint_list, filtered_guessword_list) for the team whose turn it is.'''
        team_name = self.get_team_turn()
        keyword_list, guessword_list, chosenword_list = self.get_keyword_guessword_chosenword_list(team_name)
        hint_list, filtered_guessword_list = self._spy_master.suggest(keyword_list=keyword_list,
                                                                        guessword_list=guessword_list,
                                                                        chosenword_list=chosenword_list)
        return hint_list, filtered_guessword_list

    def apply_turn(self, hint, selected_words):
        '''
        Record the current team's guess, update score, log history, and advance the turn.

        @params:
            - hint: the clue that was picked (a Hint, a synset, or None). Only kept for the
              game history log, so any printable value works.
            - selected_words: list of str, the word(s) the team guessed this turn.

        @returns: (team_name, score, required_score) for the team that just played.
        '''
        team_name = self.get_team_turn()
        self.update_chosenword_list(selected_words)
        score, required_score = self.update_team_score(team_name)

        self._game_history.append({
            'team': team_name,
            'hint': str(hint) if hint is not None else None,
            'selected_words': list(selected_words),
            'score': score,
            'required_score': required_score,
        })

        self.switch_turn()
        return team_name, score, required_score

    def is_game_over(self):
        for team_name, winning_score in zip(self._team_name_list, self._team_winning_score_list):
            if (self._team_score_dict[team_name] >= winning_score):
                return True

        return False

    def get_winner(self):
        for team_name, winning_score in zip(self._team_name_list, self._team_winning_score_list):
            if (self._team_score_dict[team_name] >= winning_score):
                return team_name

        return None

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

    def get_keyword_list(self):
        return list(self._keyword_list)

    def get_team_guessword_dict(self):
        return {team: list(words) for team, words in self._team_guessword_dict.items()}

    def get_chosen_words(self):
        return list(self._chosenword_list)

    def get_score_dict(self):
        return dict(self._team_score_dict)

    def get_game_history(self):
        return list(self._game_history)
