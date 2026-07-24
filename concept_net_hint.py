class ConceptNetHint(object):
    def __init__(self, concept_word, valid_word_count, correlated_word_list):
        '''
        @params:
            - concept_word: str, the ConceptNet concept being suggested as a clue.
            - valid_word_count: int, number of guess words in its proximity without violating forbidden words.
            - correlated_word_list: list of str, list of valid words.
        '''
        self._concept_word = concept_word
        self._valid_word_count = valid_word_count
        self._correlated_word_list = correlated_word_list

    def __str__(self):
        corr_words = '[' + ', '.join(self._correlated_word_list) + ']'
        return (f'ConceptNet clue: {self._concept_word}\n'
                f'Count: {self._valid_word_count} | Connected words: {corr_words}\n')

    def get_info(self):
        return self._concept_word, self._valid_word_count, self._correlated_word_list

    def get_label(self):
        return self._concept_word

    def get_definition(self):
        return ''

    def get_examples(self):
        return []
