from boardgame import CodenamesBoardGame

def select_game(game_idx):
    if (game_idx == 0):
        keyword_list = ['moon', 'rabbit', 'cell', 'fall', 'tokyo',
                'spine', 'board', 'force', 'bell', 'mouse',
                'ambulance', 'slip', 'line', 'triangle', 'card',
                'straw', 'death', 'hospital', 'phoenix', 'ruler',
                'doctor', 'hood', 'shop', 'band', 'march']

        team_guessword_dict = {
            'team_blue': ['cell', 'spine', 'force', 'bell', 'mouse', 'slip', 'hospital', 'hood', 'march'],
            'team_red': ['moon', 'rabbit', 'triangle', 'card', 'death', 'phoenix', 'doctor', 'band'],
        }

    elif (game_idx == 1):
        keyword_list = ['needle', 'bug', 'press', 'hawk', 'saturn',
                'jack', 'rome', 'snow', 'concert', 'cast',
                'shakespeare', 'chick', 'trip', 'canada', 'oil',
                'screen', 'triangle', 'egypt', 'mail', 'pitch',
                'center', 'queen', 'car', 'parachute', 'ray']

        team_guessword_dict = {
            'team_blue': ['needle', 'concert', 'shakespeare', 'chick', 'trip', 'screen', 'mail', 'center', 'car'],
            'team_red': ['bug', 'press', 'jack', 'canada', 'oil', 'egypt', 'pitch', 'parachute'],
        }

    else:
        keyword_list = ['dragon', 'green', 'new_york', 'australia', 'pie',
                'seal', 'wake', 'robin', 'pool', 'france',
                'trip', 'duck', 'ham', 'shark', 'grace',
                'spell', 'buck', 'dice', 'bow', 'spring',
                'tube', 'ghost', 'brush', 'drill', 'cotton']

        team_guessword_dict = {
            'team_blue': ['australia', 'wake', 'robin', 'france', 'trip', 'ham', 'grace', 'spell', 'ghost'],
            'team_red': ['dragon', 'green', 'seal', 'duck', 'shark', 'dice', 'bow', 'brush'],
        }

    return keyword_list, team_guessword_dict

def print_game(keyword_list, team_guessword_dict):
    for idx in range(5):
        print (keyword_list[idx*5:(idx+1)*5])
    print ()

    solution_list = []
    for word in keyword_list:
        if (word in team_guessword_dict['team_blue']):
            solution_list.append('|O|')
        elif (word in team_guessword_dict['team_red']):
            solution_list.append('|X|')
        else:
            solution_list.append('| |')

    for idx in range(5):
        print (solution_list[idx*5:(idx+1)*5])
    print ()

    print ('Legend')
    print ('O: Team Blue')
    print ('X: Team Red')
    print ()

if __name__ == '__main__':
    game_idx = 2
    keyword_list, team_guessword_dict = select_game(game_idx)

    game = CodenamesBoardGame(keyword_list=keyword_list, team_guessword_dict=team_guessword_dict)
    game.clear_screen()
    print_game(keyword_list, team_guessword_dict)
    game_history = game.start_game()

    print ('-'*50)
    print ('Game History')
    print (game_history)