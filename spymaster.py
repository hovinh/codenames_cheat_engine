import nltk
from nltk.corpus import wordnet as wn
import itertools
from hint import Hint

class SpyMaster(object):
    def __init__(self, similarity_method='lch'):
        '''
        @params:
            - keyword_list: list of str, 25 code words picked.
            - team_guessword_dict: dictionary of list of str. Example:
                {
                    'team_blue': ['house', 'bird', 'book', ...], # 8 words, always play first
                    'team_red': ['cat', 'dog', 'pineapple', ...], # 7 words
                }
            - chosenword_list: list of str, words have been picked.
        '''
        self._similarity_score_dict = {
            # based on the shortest path that connects the senses in the is-a (hypernym/hypnoym) taxonomy
            'path': wn.path_similarity,
            
            # based on the shortest path that connects the senses (as above) and the maximum depth of the taxonomy  
            # in which the senses occur
            'lch': wn.lch_similarity,

            # based on the depth of the two senses in the taxonomy and that of their Least Common Subsumer (most specific ancestor node)
            'wup': wn.wup_similarity,
        }
        self._similarity_method = similarity_method

    # THIS IS THE MAIN METHOD TO USE IN PLAY
    def suggest(self, keyword_list, guessword_list, chosenword_list):

        # Preprocessing: ensure do not take chosen words into account
        #print ('Before')
        #print (f'Keywords ({len(keyword_list)}): {keyword_list}')
        #print (f'Guessed words ({len(guessword_list)}): {guessword_list}')
        #print (f'Chosen words ({len(chosenword_list)}): {chosenword_list}')
        keyword_list, guessword_list, forbidword_list = self.filter_out_chosen_words(keyword_list, guessword_list, chosenword_list)
        #print ('After')
        #print (f'Keywords ({len(keyword_list)}): {keyword_list}')
        #print (f'Guessed words ({len(guessword_list)}): {guessword_list}')
        #print (f'Forbidden words ({len(forbidword_list)}): {forbidword_list}')
        
        # Step 1: retrieve all possible hypernyms (i.e. candidated word) of all guessed words
        hypernym_list_first_approach = self.retrieve_hypernym_set_with_common_approach(keyword_list, guessword_list)
        hypernym_list_second_approach = self.retrieve_hypernym_set_with_trace_to_root_approach(keyword_list, guessword_list)
        hypernym_list = list(set(hypernym_list_first_approach + hypernym_list_second_approach))

        # Step 2: for every candidated word, return if there is at least 2 guess word in proximity without violating
        # forbidden words, in decreasing order of how many guess words could be covered
        hint_list = self.generate_hints(keyword_list, forbidword_list, hypernym_list)
        
        return hint_list, guessword_list
        
    def filter_out_chosen_words(self, keyword_list, guessword_list, chosenword_list):
        keyword_list = [word for word in keyword_list if word not in chosenword_list]
        guessword_list = [word for word in guessword_list if word not in chosenword_list]
        forbidword_list = [word for word in keyword_list if word not in guessword_list]
        return keyword_list, guessword_list, forbidword_list

    def retrieve_hypernym_set_with_trace_to_root_approach(self, keyword_list, guessword_list):
        start_synset_list = self.get_synset_and_similar_from_word_list(guessword_list)
        candidated_synset_list = self.get_hypernyms_from_synset_list(start_synset_list)
        return candidated_synset_list

    def get_synset_and_similar_from_word_list(self, word_list):
        synset_list = list()
        
        for word in word_list:
            ss_list = wn.synsets(word)
            total_ss_list = [i for i in ss_list]

            for ss in ss_list:
                related_ss_list = self.get_related_synset_list_from_synset(ss)
                total_ss_list.extend(related_ss_list)

            synset_list.extend(total_ss_list)

        # filter out duplicated synsets
        synset_list = list(set(synset_list))
        return synset_list

    def get_hypernyms_from_synset_list(self, synset_list):
        hypernym_list = list()
        for ss in synset_list:
            hyper_ss_list = self.get_hypernym_up_to_root_from_synset(ss)
            hypernym_list.extend(hyper_ss_list)

        # filter out duplicated synsets
        hypernym_list = list(set(hypernym_list))
        return hypernym_list

    def get_hypernym_up_to_root_from_synset(self, synset):
        def get_hypernyms(ss):
            hyper = lambda s: s.hypernyms()
            return list(ss.closure(hyper))
        return get_hypernyms(synset)

    def retrieve_hypernym_set_with_common_approach(self, keyword_list, guessword_list):   
        traversed_synset_list = list()
        word_pair_list = self.generate_all_pairs(guessword_list)
        candidated_synset_pair_list = self.generate_all_synset_pairs_from_word_pairs(word_pair_list)
        #print (f'Original synset pairs: {len(candidated_synset_pair_list)}.')
        
        # Search for all candidated hypernyms in Breadth First Search manner
        has_new_candidate = True
        while (has_new_candidate == True):
            
            new_candidated_synset_list = []
            # Scan through all synset pairs in consideration
            for first_synset, second_synset in candidated_synset_pair_list:
                
                # The closest hypernym set covers the two synsets
                hypernym_list = first_synset.common_hypernyms(second_synset)
                #hypernym_list = first_synset.lowest_common_hypernyms(second_synset)

                # If there is a common hypernym
                if (len(hypernym_list) != 0):
                    for hypernym in hypernym_list:

                        # and we do not encounter it yet
                        if (hypernym not in traversed_synset_list):

                            # We add it to candidated hypernym set                        
                            traversed_synset_list.append(hypernym)
                            new_candidated_synset_list.append(hypernym)
            
            # Stop scanning if no new candidate found
            if (len(new_candidated_synset_list) == 0):
                has_new_candidate = False

            # otherwise, generate new pairs of synset
            else:
                cur_candidate_synset_list = self.filter_unique_synset_from_synset_pairs_list(candidated_synset_pair_list)
                new_candidated_synset_list = new_candidated_synset_list + cur_candidate_synset_list
                candidated_synset_pair_list = self.generate_all_pairs(new_candidated_synset_list)
                #print (f'New synset pairs: {len(candidated_synset_pair_list)}.')

        #print (f'Official retrieved hypernyms: {len(traversed_synset_list)}.')
        return traversed_synset_list
                            
    def generate_hints(self, keyword_list, forbidword_list, hypernym_list):
        synset_word_dict = self.generate_synset_word_dict(keyword_list)
        all_synset_list = self.generate_all_synset_from_word_list(keyword_list)
        
        raw_hint_count_list = []
        # determine method to compute word similarity
        compute_sim = self._similarity_score_dict[self._similarity_method]

        for hypernym in hypernym_list:

            # only compute similarity when two synonyms have the same POS, otherwise 0, i.e. minimal similarity
            hypernym_POS = hypernym.pos()
            symset_score_dict = {ss: compute_sim(hypernym, ss) if hypernym_POS == ss.pos() else 0 for ss in all_synset_list}

            # the score of a hypernym to a synset is the WORD in KEYWORD (NOT LEMMA) closest to it, i.e. highest similarity score
            word_score_dict = self.simplify_score_symset_to_word(symset_score_dict, synset_word_dict)
            sorted_word_descending_score_list = sorted(word_score_dict.items(), key=lambda x: x[1], reverse=True)
            
            # compute number of guesses possible
            sorted_word_list = [word for word, count in sorted_word_descending_score_list] 
            can_be_selected = False
            valid_word_count = 0
            correlated_word_list = list()
            for word in sorted_word_list:
                if (word in forbidword_list):
                    break
                else:
                    valid_word_count += 1
                    if (valid_word_count >= 2):
                        can_be_selected = True
                    correlated_word_list.append(word)
                    
            if (can_be_selected == True):
                raw_hint_count_list.append([Hint(synset=hypernym, valid_word_count=valid_word_count, correlated_word_list=correlated_word_list), valid_word_count])
                
        #print (f'Filtered hypernyms: {len(hint_list)}.')
        word_count_idx = 1
        sorted_hint_count_list = sorted(raw_hint_count_list, key=lambda x: x[word_count_idx], reverse=True)
        hint_list = [ele[0] for ele in sorted_hint_count_list]
        return hint_list

    def simplify_score_symset_to_word(self, symset_score_dict, synset_word_dict):
        word_score_dict = dict()
        for ss, score in symset_score_dict.items():
            word = synset_word_dict[ss]

            if (word not in word_score_dict.keys()):
                word_score_dict[word] = score
            elif (score > word_score_dict[word]):
                word_score_dict[word] = score
                
        return word_score_dict

    """ UTILS """
    def generate_all_pairs(self, element_list):
        return list(itertools.combinations(element_list, 2))

    def generate_all_synset_pairs_from_word_pairs(self, word_pair_list):
        synset_pair_list = []
        for first_word, second_word in word_pair_list:
            first_synset_list = wn.synsets(first_word)
            second_synset_list = wn.synsets(second_word)
            
            for ss1 in first_synset_list:
                for ss2 in second_synset_list:
                    synset_pair_list.append([ss1, ss2])
                    
        return synset_pair_list

    def generate_all_synset_from_word_list(self, word_list):
        synset_list = list()
        for word in word_list:
            ss_list = wn.synsets(word)
            synset_list.extend(ss_list)

        return synset_list

    def generate_word_synset_dict(self, word_list):
        word_synset_dict = dict()
        for word in word_list:
            ss_list = wn.synsets(word)
            word_synset_dict[word] = ss_list

        return word_synset_dict
        
    def generate_synset_word_dict(self, word_list, include_related=True):
        synset_word_dict = dict()
        for word in word_list:
            ss_list = wn.synsets(word)
            total_ss_list = [i for i in ss_list]

            if (include_related == True):
                for ss in ss_list:
                    related_ss_list = self.get_related_synset_list_from_synset(ss)
                    total_ss_list.extend(related_ss_list)

            for ss in total_ss_list: 
                # Maybe it's possible 2 words belong to the same synset, but we assume it's NOT for now
                synset_word_dict[ss] = word
            
        return synset_word_dict

    def get_related_synset_list_from_synset(self, synset):
        # Generate all synsets:
            # - synset also see for the synset of the word
            # - synset similar to the synset of the word
        also_sees_ss_list = synset.also_sees()
        similar_tos_ss_list = synset.similar_tos()
        related_ss_list = also_sees_ss_list + similar_tos_ss_list
        return related_ss_list
    
    def filter_unique_synset_from_synset_pairs_list(self, ss_pairs_list):
        ss_list = list(set([ss for ss_pair in ss_pairs_list for ss in ss_pair]))
        return ss_list