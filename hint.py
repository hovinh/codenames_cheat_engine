class Hint(object):
    def __init__(self, synset, valid_word_count, correlated_word_list):
        '''
        @params:
            - synset: a WordNet synset object.
            - valid_word_count: int, number of guess words in its proximity without violating forbidden words
            - correlated_word_list: list of str, list of valid words
        '''
        self._synset = synset
        self._valid_word_count = valid_word_count
        self._correlated_word_list = correlated_word_list

    def __str__(self):
        synset_str = str(self._synset)
        definition = self._synset.definition()
        examples = '[' + '| '.join(self._synset.examples()) + ']'
        lemmas = '[' + ', '.join([l.name() for l in self._synset.lemmas()]) + ']'
        corr_words = '[' + ', '.join(self._correlated_word_list) + ']'
            
        returned_str = (f'Synset {synset_str} | Definition: {definition}\n'
                        f'Examples: {examples}\n'
                        f'Count: {self._valid_word_count} | Lemmas: {lemmas} | Connected words: {corr_words}\n')

        return returned_str

    def get_info(self):
        return self._synset, self._valid_word_count, self._correlated_word_list
