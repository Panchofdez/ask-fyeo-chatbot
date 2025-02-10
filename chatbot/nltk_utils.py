import nltk
# nltk.download('punkt')
# nltk.download('punkt_tab')
# nltk.download('wordnet')
import numpy as np
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
import string


stemmer = PorterStemmer()
lemmer = WordNetLemmatizer()

def tokenize(sentence):
    return nltk.word_tokenize(sentence)

def bigrams(sentence):
    return [ f"{t1} {t2}" for t1, t2 in list(nltk.bigrams(nltk.word_tokenize(sentence)))]

def stem(word):
    return stemmer.stem(word.lower())

def remove_links(response):
    links = []
    link_tag = ""
    start = False
    for i in range(len(response)):
        char = response[i]
        if char == "<" or start:
            link_tag += char
            start = True
        if char == ">" and start:
            links.append(link_tag)
            link_tag = ""
            start = False
            
    for link in links:
        response = response.replace(link, "")
        
    return response

def bag_of_words(tokenized_sentence, all_words):
    bag = np.zeros(len(all_words), dtype=np.float32)
    tokenized_sentence = [lemmer.lemmatize(w) for  w in tokenized_sentence]
    for idx, w in enumerate(all_words):
        if w in tokenized_sentence:
            bag[idx] = 1.0
    return bag


def clean_lemmatize(text):
    stop_punc_words = set(list(string.punctuation))
    stop_punc_words.add("<a>")
    stop_punc_words.add("</a>")
    stop_punc_words.add("href")
    filtered_text = [token.lower() for token in clean_links(text.lower()).split() if token not in stop_punc_words and len(token) > 2 and token.find("'") == -1]
    # print("FILTERED", filtered_text)
    return " ".join([lemmer.lemmatize(token) for token in filtered_text])

def clean_links(text):
    is_link = False
    result = ""
    for char in text:
        if char == "<":
            is_link = True
        elif not is_link:
            result += char
        elif char == ">":
            is_link = False
            
    return result


def remove_punc(text):
    stop_punc_words = set(list(string.punctuation))
    filtered_text = "".join([char for char in text if char not in stop_punc_words])
    return filtered_text       