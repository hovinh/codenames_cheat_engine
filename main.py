import os
import questionary
from nltk.corpus import wordnet as wn
from boardgame import CodenamesBoardGame
from sample_games import select_game, print_game

def clear_screen():
    # Source: https://www.geeksforgeeks.org/clear-screen-python/
    # for windows
    if (os.name == 'nt'):
        _ = os.system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')

def select_hint_and_guesswords(hint_list, guessword_list, do_clear_screen=True):
    selected_idx = 0
    numb_candidates_shown = 8
    numb_candidates_total = len(hint_list)

    # If there is hint can lead to 2 words at least
    if (numb_candidates_total > 0):
        if (do_clear_screen == True):
            clear_screen()

        while (True):
            if (do_clear_screen == True):
                clear_screen()

            selected_idx_max = min(selected_idx+numb_candidates_shown, numb_candidates_total)
            candidate_idx_list = [i for i in range(selected_idx, selected_idx_max, 1)]
            next_idx = candidate_idx_list[-1] + 1

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
            clear_screen()

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

def run_cli_game(game):
    while (game.is_game_over() == False):
        team_name = game.get_team_turn()
        print (f"This is {team_name}'s turn.")

        hint_list, filtered_guessword_list = game.get_suggestions()
        selected_hint, selected_words = select_hint_and_guesswords(hint_list, filtered_guessword_list)
        print (f"Selected hint: {selected_hint} | Selected guessed words: {selected_words}")

        team_name, score, required_score = game.apply_turn(selected_hint, selected_words)
        print (f'Updated score: {score}/{required_score}')

    print (f'The winner is {game.get_winner()}!!!')
    return game.get_game_history()

if __name__ == '__main__':
    game_idx = 2
    keyword_list, team_guessword_dict = select_game(game_idx)

    game = CodenamesBoardGame(keyword_list=keyword_list, team_guessword_dict=team_guessword_dict)
    clear_screen()
    print_game(keyword_list, team_guessword_dict)
    game_history = run_cli_game(game)

    print ('-'*50)
    print ('Game History')
    print (game_history)
