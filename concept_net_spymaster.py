import concept_net_data
from clue_safety import is_related_to_board_word
from concept_net_hint import ConceptNetHint


class ConceptNetSpyMaster(object):
    def __init__(self, min_weight=1.0):
        '''
        @params:
            - min_weight: float, minimum ConceptNet edge weight for a neighbor to
              count as related. ConceptNet's RelatedTo weights start around 1.0
              for reliable assertions; raise this to tighten suggestions.
        '''
        self._min_weight = min_weight

    # THIS IS THE MAIN METHOD TO USE IN PLAY
    def suggest(self, keyword_list, guessword_list, chosenword_list):
        filtered_keyword_list, filtered_guessword_list, forbidword_list = self.filter_out_chosen_words(
            keyword_list, guessword_list, chosenword_list)

        neighbor_maps = {word: concept_net_data.get_related_concepts(word) for word in filtered_guessword_list}
        forbidden_neighbor_words = set()
        for forbid_word in forbidword_list:
            forbidden_neighbor_words.update(concept_net_data.get_related_concepts(forbid_word).keys())

        candidate_words = set()
        for neighbors in neighbor_maps.values():
            candidate_words.update(neighbors.keys())

        hint_list = self.generate_hints(filtered_keyword_list, filtered_guessword_list, forbidword_list,
                                         candidate_words, neighbor_maps, forbidden_neighbor_words)
        return hint_list, filtered_guessword_list

    def filter_out_chosen_words(self, keyword_list, guessword_list, chosenword_list):
        keyword_list = [word for word in keyword_list if word not in chosenword_list]
        guessword_list = [word for word in guessword_list if word not in chosenword_list]
        forbidword_list = [word for word in keyword_list if word not in guessword_list]
        return keyword_list, guessword_list, forbidword_list

    def generate_hints(self, keyword_list, guessword_list, forbidword_list,
                        candidate_words, neighbor_maps, forbidden_neighbor_words):
        raw_hints = []
        for candidate in candidate_words:
            # covers "candidate is literally a board word" (exact match) as well as forms of one
            if is_related_to_board_word(candidate, keyword_list):
                continue
            if candidate in forbidden_neighbor_words:
                continue

            covered = [word for word in guessword_list
                       if neighbor_maps[word].get(candidate, 0.0) >= self._min_weight]
            if len(covered) < 2:
                continue

            score = sum(neighbor_maps[word][candidate] for word in covered)
            raw_hints.append((ConceptNetHint(candidate, len(covered), covered), score))

        raw_hints.sort(key=lambda pair: pair[1], reverse=True)
        return [hint for hint, _ in raw_hints]
