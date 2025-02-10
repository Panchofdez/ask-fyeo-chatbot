
# import random
# from .chatbot_abstract import Chatbot
# from sentence_transformers import SentenceTransformer, util
# from .nltk_utils import remove_punc, tokenize, stem


# class SBERTChatbot(Chatbot):
#     def __init__(self):
#         self.sbert = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
#     def train(self, data):
#         pattern_tag_map = {}
#         all_patterns = []
#         duplicates = []
#         for intent in data["intents"]:
#             patterns = intent["patterns"]
#             tag = intent["tag"]
    
#             for sent in patterns:
#                 clean_sent = remove_punc(sent.lower())
#                 if clean_sent in pattern_tag_map and pattern_tag_map[clean_sent] != tag: 
#                     print("DUPLICATE FOUND", sent, tag, pattern_tag_map[clean_sent] )
#                     duplicates.append((tag, clean_sent, pattern_tag_map[clean_sent]))
#                 pattern_tag_map[clean_sent] = tag
#                 all_patterns.append(clean_sent)
                
#         pattern_embeddings = self.sbert.encode(all_patterns)
                    
#         for intent in data["intents"]:
#             patterns = intent["patterns"]
#             tag = intent["tag"]
    
#             for sent in patterns:
#                 clean_sent = remove_punc(sent.lower())
#                 query_embedding = self.sbert.encode(clean_sent)
                

#                 # similarity = self.sentence_transformer_model.similarity(query_embedding, pattern_embeddings)
#                 # print("SIMILARITY", similarity)
#                 scores = util.dot_score(query_embedding, pattern_embeddings)[0].cpu().tolist()
            
#                 pattern_score_pairs = list(zip(all_patterns, scores))
                
#                 #Sort by decreasing score
#                 pattern_score_pairs = sorted(pattern_score_pairs, key=lambda x: x[1], reverse=True)
                
#                 # #Output passages & scores
#                 # print("TOP DOT SCORES FOR: ", clean_sent)
#                 # for pattern, score in pattern_score_pairs[:10]:
#                 #     print(score, pattern)
                    
#                 target_pattern, target_score = pattern_score_pairs[0]
#                 target_tag = pattern_tag_map[target_pattern]
                
#                 if target_score > 0.9 and target_tag != tag:
#                     duplicates.append((target_tag, target_pattern, tag, clean_sent, target_score))
                    
#         print("FOUND THE FOLLOWING DUPLICATES")
#         for dup in duplicates:
#             print(dup)
               
#         return
    
#     def get_response(self, query, data, file=None): 
#         default_answer = ("", "Hmm... I do not understand that question. If I cannot answer your question you can email firstyeareng@torontomu.ca or stop by our office (located: ENG340A) Monday to Friday from 9 am to 4 pm. Please try again or ask a different question.")
#         pattern_tag_map = {}
#         all_patterns = []
        
#         for intent in data["intents"]:
#             patterns = intent["patterns"]
#             tag = intent["tag"]
    
#             for sent in patterns:
#                 clean_sent = remove_punc(sent.lower())
#                 pattern_tag_map[clean_sent] = tag
#                 all_patterns.append(clean_sent)
                
#         query_embedding = self.sbert.encode(remove_punc(query.lower()))
#         pattern_embeddings = self.sbert.encode(all_patterns)

#         # similarity = self.sentence_transformer_model.similarity(query_embedding, pattern_embeddings)
#         # print("SIMILARITY", similarity)
#         scores = util.dot_score(query_embedding, pattern_embeddings)[0].cpu().tolist()
        
#         pattern_score_pairs = list(zip(all_patterns, scores))
        
#         #Sort by decreasing score
#         pattern_score_pairs = sorted(pattern_score_pairs, key=lambda x: x[1], reverse=True)

#         # #Output passages & scores
#         # print("DOT SCORE")
#         # for pattern, score in pattern_score_pairs[:20]:
#         #     print(score, pattern)
            
#         target_pattern, target_score = pattern_score_pairs[0]
#         target_tag = pattern_tag_map[target_pattern]
#         result = (target_tag, target_pattern, target_score)
#         print("FINAL ANSWER", result)
        
#         if target_score > 0.7:
#             for intent in data["intents"]:
#                 if target_tag == intent["tag"]:
#                     resp = random.choice(intent['responses'])     
#                     if self.check_response(intent["tag"], intent['patterns'], query, resp):
#                         return  (target_tag, f"{resp}")
            
#         return default_answer
    
#     def chat(self, data, file=None):
#         bot_name="Sam"
#         while True:
#             sentence = input('You: ')
#             if sentence == "quit" or sentence == "q":
#                 break

#             print(f"{bot_name} {self.get_response(sentence, data)[1]}")

#         return
    
#     def check_response(self, tag, patterns, question, response):
#         '''
#         Determines the validity of the chatbot's response
#         '''
       
#         question = tokenize(question)
#         patterns = ' '.join(patterns)
#         ignore_words = ['?', '!', '.', ',', 'are', 'you', 'can', 'and', 'let','where', 'why', 'what', 'how' , 'when', 'who', 'the' , 'need', 'for', 'have', 'but']
#         stemmed_words  = [stem(w) for w in question if w.lower() not in ignore_words and len(w) > 2 ] # avoid punctuation or words like I , a , or 

#         if len(stemmed_words) == 0:
#             stemmed_words = [stem(w) for w in question]

#         found = [ w for w in stemmed_words if re.search(w.lower(), response.lower()) or re.search(w.lower(),tag.lower() ) != None or re.search(w.lower(), patterns.lower())] #check if the question has words related in the response
#         print("FOUND", found)
#         return len(found) > 0
    
#     def find_duplicate(self, data, query):
#         pattern_tag_map = {}
#         all_patterns = []
#         duplicates = []
#         for intent in data["intents"]:
#             patterns = intent["patterns"]
#             tag = intent["tag"]
    
#             for sent in patterns:
#                 clean_sent = remove_punc(sent.lower())
#                 pattern_tag_map[clean_sent] = tag
#                 all_patterns.append(clean_sent)
                
#         pattern_embeddings = self.sbert.encode(all_patterns)
#         query_embedding = self.sbert.encode(remove_punc(query.lower))
        
#         # similarity = self.sentence_transformer_model.similarity(query_embedding, pattern_embeddings)
#         # print("SIMILARITY", similarity)
#         scores = util.dot_score(query_embedding, pattern_embeddings)[0].cpu().tolist()
    
#         pattern_score_pairs = list(zip(all_patterns, scores))
        
#         #Sort by decreasing score
#         pattern_score_pairs = sorted(pattern_score_pairs, key=lambda x: x[1], reverse=True)
        
#         # #Output passages & scores
#         # print("TOP DOT SCORES FOR: ", clean_sent)
#         # for pattern, score in pattern_score_pairs[:10]:
#         #     print(score, pattern)
            
#         target_pattern, target_score = pattern_score_pairs[0]
#         target_tag = pattern_tag_map[target_pattern]
        
#         if target_score > 0.9 and target_tag != tag:
#             duplicates.append((target_tag, target_pattern, tag, clean_sent, target_score))
                    
#         print("FOUND THE FOLLOWING DUPLICATES")
#         for dup in duplicates:
#             print(dup)
               
