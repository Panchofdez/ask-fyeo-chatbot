
# import re
# import random
# from .chatbot_abstract import Chatbot
# from sentence_transformers.cross_encoder import CrossEncoder
# from sentence_transformers import SentenceTransformer, util

# from .nltk_utils import remove_punc, tokenize, stem



# class STChatbot(Chatbot):
    
#     def __init__(self):
#         # self.sentence_transformer_model = CrossEncoder("cross-encoder/stsb-distilroberta-base")
#         self.sentence_transformer_model = SentenceTransformer("multi-qa-mpnet-base-cos-v1")
    
#     def train(self, data):
#         sentence_tag_map = {}
#         all_sentences = []
#         duplicates = []
#         for intent in data["intents"]:
#             sentences = intent["patterns"]
#             tag = intent["tag"]
    
#             for sent in sentences:
#                 clean_sent = remove_punc(sent.lower())
#                 if clean_sent in sentence_tag_map and sentence_tag_map[clean_sent] != tag: 
#                     print("DUPLICATE FOUND", sent, tag, sentence_tag_map[clean_sent] )
#                     duplicates.append((tag, clean_sent, sentence_tag_map[clean_sent]))
#                 sentence_tag_map[clean_sent] = tag
#                 all_sentences.append(clean_sent)
                
#         pattern_embeddings = self.sentence_transformer_model.encode(all_sentences)
                
        
#         for intent in data["intents"]:
#             sentences = intent["patterns"]
#             tag = intent["tag"]
    
#             for sent in sentences:
#                 clean_sent = remove_punc(sent.lower())
#                 query_embedding = self.sentence_transformer_model.encode(clean_sent)
                

#                 # similarity = self.sentence_transformer_model.similarity(query_embedding, pattern_embeddings)
#                 # print("SIMILARITY", similarity)
#                 scores = util.dot_score(query_embedding, pattern_embeddings)[0].cpu().tolist()
            
#                 pattern_score_pairs = list(zip(all_sentences, scores))
                
#                 #Sort by decreasing score
#                 pattern_score_pairs = sorted(pattern_score_pairs, key=lambda x: x[1], reverse=True)
                
#                 # #Output passages & scores
#                 # print("TOP DOT SCORES FOR: ", clean_sent)
#                 # for pattern, score in pattern_score_pairs[:10]:
#                 #     print(score, pattern)
                    
#                 target_pattern, target_score = pattern_score_pairs[0]
#                 target_tag = sentence_tag_map[target_pattern]
                
#                 if target_score > 0.9 and target_tag != tag:
#                     duplicates.append((target_tag, target_pattern, tag, clean_sent, target_score))
                    
#         print("FOUND THE FOLLOWING DUPLICATES")
#         for dup in duplicates:
#             print(dup)
               
#         return
    
#     def get_response(self, query, data, file=None): 
#         default_answer = ("", "Hmm... I do not understand that question. Please try again or ask a different question")
#         sentence_tag_map = {}
#         all_sentences = []
        
#         for intent in data["intents"]:
#             sentences = intent["patterns"]
#             tag = intent["tag"]
    
#             for sent in sentences:
#                 clean_sent = remove_punc(sent.lower())
#                 sentence_tag_map[clean_sent] = tag
#                 all_sentences.append(clean_sent)
                
#         query_embedding = self.sentence_transformer_model.encode(query)
#         pattern_embeddings = self.sentence_transformer_model.encode(all_sentences)

#         # similarity = self.sentence_transformer_model.similarity(query_embedding, pattern_embeddings)
#         # print("SIMILARITY", similarity)
#         scores = util.dot_score(query_embedding, pattern_embeddings)[0].cpu().tolist()
        
#         pattern_score_pairs = list(zip(all_sentences, scores))
        
#         #Sort by decreasing score
#         pattern_score_pairs = sorted(pattern_score_pairs, key=lambda x: x[1], reverse=True)

#         # #Output passages & scores
#         # print("DOT SCORE")
#         # for pattern, score in pattern_score_pairs[:20]:
#         #     print(score, pattern)
            
#         target_pattern, target_score = pattern_score_pairs[0]
#         target_tag = sentence_tag_map[target_pattern]
#         result = (target_tag, target_pattern, target_score)
#         print("FINAL ANSWER", result)
        
#         for intent in data["intents"]:
#             if target_tag == intent["tag"]:
#                 resp = random.choice(intent['responses'])     
#                 if self.check_response(intent["tag"], intent['patterns'], query, resp):
#                     return  (target_tag, f"{resp}")
            
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
    