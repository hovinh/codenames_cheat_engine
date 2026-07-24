def is_related_to_board_word(candidate_word, board_words, min_shared_length=4):
    '''
    Mirrors Codenames' "a clue can't be a form of a word on the board" rule via a
    substring heuristic (e.g. "seal" vs "sealed", "grace" vs "disgrace").

    @params:
        - candidate_word: str, the word being considered as a clue.
        - board_words: list of str, words currently on the board.
        - min_shared_length: int, words shorter than this are exempt from the
          substring check (otherwise short words like "a" or "an" would collide
          with almost everything).
    @returns: bool, True if candidate_word is (a form of) a board word.
    '''
    candidate = candidate_word.lower().replace('_', '').replace(' ', '')
    for board_word in board_words:
        board = board_word.lower().replace('_', '').replace(' ', '')
        if candidate == board:
            return True
        if len(candidate) >= min_shared_length and len(board) >= min_shared_length:
            if candidate in board or board in candidate:
                return True
    return False
