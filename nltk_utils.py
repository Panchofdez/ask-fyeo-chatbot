import nltk
#nltk.download('punkt')
import numpy as np
from nltk.stem.porter import PorterStemmer

stemmer = PorterStemmer()

def tokenize(sentence):
    return nltk.word_tokenize(sentence)

def stem(word):
    return stemmer.stem(word.lower())


def bag_of_words(tokenized_sentence, all_words):
    
    bag = np.zeros(len(all_words), dtype=np.float32)
    tokenized_sentence = [stem(w) for  w in tokenized_sentence]
    for idx, w in enumerate(all_words):
        if w in tokenized_sentence:
            bag[idx] = 1.0
    return bag

a ="How do I book an advising appointment?"

# print(a)
# a = tokenize(a)
# print(a)
# stemmed_words  = [stem(w) for w in a ]

# print(stemmed_words)

# print(bag_of_words(a))