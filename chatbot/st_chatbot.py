
import re
import random
from .chatbot_abstract import Chatbot
from sentence_transformers.cross_encoder import CrossEncoder
from .nltk_utils import remove_punc, tokenize, stem



class STChatbot(Chatbot):
    
    def __init__(self):
        self.sentence_transformer_model = CrossEncoder("cross-encoder/stsb-distilroberta-base")
    
    def train(self):
        return
    
    def get_response(self, query, data, file=None): 

        default_answer = ("", "Hmm... I do not understand that question. Please try again or ask a different question")
        # final_scores = []
        sentence_tag_map = {}
        all_sentences = []
        
        for intent in data["intents"]:
            sentences = intent["patterns"]
            tag = intent["tag"]
    
            for sent in sentences:
                clean_sent = remove_punc(sent.lower())
                sentence_tag_map[clean_sent] = tag
                all_sentences.append(clean_sent)
                
                
        # print("SENTENCES", all_sentences)
                
                
        ranks = self.sentence_transformer_model.rank(remove_punc(query.lower()), all_sentences)

        high_score = None
        high_scores = []
        for rank in ranks:
            # print(f"{rank['score']:.2f}\t{sentences[rank['corpus_id']]}")
            if high_score is None or (rank['score'] > high_score and rank['score'] > 0.5):
                high_score = rank['score']
                target_tag = sentence_tag_map[all_sentences[rank['corpus_id']]]
                high_scores.append((target_tag, high_score))

        print("MAX_SCORE", high_score, target_tag)
        score_result = (target_tag, high_score)
            # print("HIGH_SCORE", high_score)
            # final_scores.append((tag, high_score, random.choice(intent["responses"])))
        
        # print("FINAL SCORES", final_scores)
        # max_score = None
        # high_scores = []
        # for tag, score, resp in final_scores:
        #     if (max_score is None or score > max_score) and score > 0.45:
        #         result = (tag, resp)
        #         max_score = score
        #         high_scores.append((tag, score))

        # print("MAX_SCORE", max_score)    
        print("HIGH SCORES", high_scores[-5:])    
        print("FINAL RESULT", score_result)        
        for intent in data["intents"]:
            if score_result[0] == intent["tag"]:
                resp = random.choice(intent['responses'])     
                if self.check_response(intent["tag"], intent['patterns'], query, resp):
                    return  (score_result[0], f"{resp}")
   
        return default_answer

    
    def chat(self, data, file=None):
        bot_name="Sam"
        while True:
            sentence = input('You: ')
            if sentence == "quit" or sentence == "q":
                break

            print(f"{bot_name} {self.get_response(sentence, data)[1]}")

        return
    
    def check_response(self, tag, patterns, question, response):
        '''
        Determines the validity of the chatbot's response
        '''
       
        question = tokenize(question)
        patterns = ' '.join(patterns)
        #print("Question", question)
        #print('Patterns',patterns)
        # print("Response", response)
        ignore_words = ['?', '!', '.', ',', 'are', 'you', 'can', 'and', 'let','where', 'why', 'what', 'how' , 'when', 'who', 'the' , 'need', 'for', 'have', 'but']
        stemmed_words  = [stem(w) for w in question if w.lower() not in ignore_words and len(w) > 2 ] # avoid punctuation or words like I , a , or 
        

        if len(stemmed_words) == 0:
            stemmed_words = [stem(w) for w in question]

        #print(stemmed_words)

        found = [ w for w in stemmed_words if re.search(w.lower(), response.lower()) or re.search(w.lower(),tag.lower() ) != None or re.search(w.lower(), patterns.lower())] #check if the question has words related in the response
        print("FOUND", found)
        return len(found) > 0
    