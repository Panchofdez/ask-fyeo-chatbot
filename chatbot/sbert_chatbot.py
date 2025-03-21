
import random
from .chatbot_abstract import Chatbot
from sentence_transformers import SentenceTransformer, util
from .nltk_utils import remove_punc, tokenize, stem
import re


class SBERTChatbot(Chatbot):
    def __init__(self):
        self.sbert = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.all_patterns = []
        self.pattern_tag_map = {}
        self.pattern_embeddings = []
    
    def train(self, data):
        self.analyze_faq(data)
        return
        
    def process_faq(self, data, duplicates=[]):
        process_embeddings = False
        all_patterns = []
        pattern_tag_map = {}

        for intent in data["intents"]:
            patterns = intent["patterns"]
            tag = intent["tag"]
    
            for sent in patterns:
                clean_sent = remove_punc(sent.lower())
                if clean_sent in pattern_tag_map and pattern_tag_map[clean_sent] != tag:
                    duplicates.append((pattern_tag_map[clean_sent], clean_sent, tag, clean_sent, 1.0))

                pattern_tag_map[clean_sent] = tag
                all_patterns.append(clean_sent)

                if clean_sent not in self.pattern_tag_map:
                    process_embeddings = True
                
        if process_embeddings:
            self.pattern_embeddings = self.sbert.encode(all_patterns)
            self.all_patterns = all_patterns
            self.pattern_tag_map = pattern_tag_map
    
    def get_response(self, query, data, file=None): 
        default_answer = ("", "Hmm... I do not understand that question. If I cannot answer your question you can email firstyeareng@torontomu.ca or stop by our office (located: ENG340A) Monday to Friday from 9 am to 4 pm. Please try again or ask a different question.")
        self.process_faq(data)         
        query_embedding = self.sbert.encode(remove_punc(query.lower()))

        # similarity = self.sentence_transformer_model.similarity(query_embedding, pattern_embeddings)
        scores = util.dot_score(query_embedding, self.pattern_embeddings)[0].cpu().tolist()
        
        #Sort by decreasing score
        pattern_score_pairs = sorted(list(zip(self.all_patterns, scores)), key=lambda x: x[1], reverse=True)
            
        target_pattern, target_score = pattern_score_pairs[0]
        target_tag = self.pattern_tag_map[target_pattern]
        result = (target_tag, target_pattern, target_score)
        # print("FINAL ANSWER", result)
        
        if target_score > 0.7:
            for intent in data["intents"]:
                if target_tag == intent["tag"]:
                    resp = random.choice(intent['responses'])     
                    if self.check_response(intent["tag"], intent['patterns'], query, resp):
                        return (target_tag, f"{resp}")
            
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
        ignore_words = ['?', '!', '.', ',', 'are', 'you', 'can', 'and', 'let','where', 'why', 'what', 'how' , 'when', 'who', 'the' , 'need', 'for', 'have', 'but']
        stemmed_words  = [stem(w) for w in question if w.lower() not in ignore_words and len(w) > 2 ] # avoid punctuation or words like I , a , or 

        if len(stemmed_words) == 0:
            stemmed_words = [stem(w) for w in question]

        found = [ w for w in stemmed_words if re.search(w.lower(), response.lower()) or re.search(w.lower(),tag.lower() ) != None or re.search(w.lower(), patterns.lower())] #check if the question has words related in the response
        # print("FOUND", found)
        return len(found) > 0
    
    def find_duplicates(self, data, tag, patterns):
        print("FIND DUPLICATES")
        self.process_faq(data)
        duplicates = set()
        for query in patterns:
            query_embedding = self.sbert.encode(remove_punc(query.lower()))
        
            # similarity = self.sentence_transformer_model.similarity(query_embedding, pattern_embeddings)
            scores = util.dot_score(query_embedding, self.pattern_embeddings)[0].cpu().tolist() 
            
            #Sort by decreasing score
            pattern_score_pairs = sorted(list(zip(self.all_patterns, scores)), key=lambda x: x[1], reverse=True)

            #Output passages & scores
            # print(f"TOP DOT SCORES FOR: {pattern} - {tag}")

            for target_pattern, target_score in pattern_score_pairs:
                target_tag = self.pattern_tag_map[target_pattern]     
                if target_score >= 0.95 and target_tag != tag:
                    print(f"({target_tag}, {target_pattern}) -> ({tag}, {query}) -> {target_score}")
                    duplicates.add(query)
                elif target_score < 0.95:
                    break
                
        print("FOUND THE FOLLOWING DUPLICATES")
        for dup in duplicates:
            print(dup)
                
        return list(duplicates)
               

    def analyze_faq(self, data):

        duplicates = []
        self.process_faq(data, duplicates)
        for i in range(len(self.pattern_embeddings)):
            query_embedding = self.pattern_embeddings[i]
            pattern = self.all_patterns[i]
            tag = self.pattern_tag_map[pattern]
            
            # scores = util.dot_score(query_embedding, pattern_embeddings)[0].cpu().tolist()   
            scores = util.cos_sim(query_embedding, self.pattern_embeddings)[0].cpu().tolist()
        
            #Sort by decreasing score
            pattern_score_pairs = sorted(list(zip(self.all_patterns, scores)), key=lambda x: x[1], reverse=True)
            
            #Output passages & scores
            # print(f"TOP DOT SCORES FOR: {pattern} - {tag}")
            for target_pattern, target_score in pattern_score_pairs[:10]:
                target_tag = self.pattern_tag_map[target_pattern]
                if target_score > 0.95 and target_tag != tag:
                    # print(target_score, pattern)
                    duplicates.append((target_tag, target_pattern, tag, pattern, target_score))
                
        print("FOUND THE FOLLOWING DUPLICATES")
        for dup in duplicates:
            print(dup)
                
        return

