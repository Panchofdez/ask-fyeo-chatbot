from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .nltk_utils import remove_punc



class TFIDF():
    def find_duplicates(data, target_tag, target_patterns):
        all_patterns = []
        for intent in data["intents"]:
            patterns = intent["patterns"]
            tag = intent["tag"]

            if tag == target_tag:
                continue

            for sent in patterns:
                clean_sent = remove_punc(sent.lower())
                all_patterns.append(clean_sent)
        
        start_index = len(all_patterns)
        target_index = start_index

        for pattern in target_patterns:
            all_patterns.append(remove_punc(pattern.lower()))

        # Convert all sentences to TF-IDF vectors
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(all_patterns)
        duplicates_set = set()

        for pattern in target_patterns:
            # print("TARGET PATTERN", pattern)
            target_vector = tfidf_matrix[target_index]

            # Compute similarity between target and all other sentences
            similarities = cosine_similarity(target_vector, tfidf_matrix).flatten()

            threshold = 0.8
            duplicates = [(i, all_patterns[i], sim) for i, sim in enumerate(similarities) if sim > threshold and i < start_index]

            # Print results
            if duplicates:
                # print("Duplicate sentences found:")
                # for idx, dup_sentence, score in duplicates:
                #     print(f"- Sentence {idx}: '{dup_sentence}' (Similarity: {score:.2f})")
                duplicates_set.add(pattern)
            # else:
            #     print("No duplicates found.")

            target_index += 1
        # print("FOUND THE FOLLOWING DUPLICATES")
        # for dup in duplicates_set:
        #     print(dup)
                
        return list(duplicates_set)