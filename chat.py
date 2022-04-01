import random
import json
import torch
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize


def classify(sentence, model, all_words, tags):
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]
    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    results = [ (i, p) for i, p in enumerate(probs.detach().numpy()[0])  if p > 0.5]
    results.sort(key=lambda x: x[1], reverse=True)
    print(results)
    return_list = []
    for r in results:
        return_list.append((tags[r[0]], r[1]))

    return return_list




def chatbot(sentence, data, model,intents, userId='123', context={}, show_details=True):
    
    print("INTENTS" , intents)
    sentence = tokenize(sentence)
    results = classify(sentence, model, all_words=data["all_words"], tags=data["tags"])
    print("FINAL RESULTS: ",results)

    while results:
        for intent in intents["intents"]:
            if results[0][0] == intent["tag"]:
                print(context, intent)

                if 'context_set' in intent:
                    if show_details: print ('context:', intent['context_set'])
                    context[userId] = intent['context_set']

                if not 'context_filter' in intent or \
                (userId in context and 'context_filter' in intent and intent['context_filter'] == context[userId]):
                    print("FOUND ANSWER")
                    return  (intent["tag"], f"{random.choice(intent['responses'])}")
        results.pop(0) 

    return ("" , "I do not understand please try again or ask another question ... ")


def chat():
    

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    with open('intents.json', 'r', encoding="utf8") as f:
        intents = json.load(f)


    FILE = "data.pth"
    data = torch.load(FILE)

    input_size = data["input_size"]
    hidden_size = data["hidden_size"]
    output_size = data["output_size"]
    all_words = data["all_words"]
    tags = data["tags"]
    model_state = data["model_state"]

    model = NeuralNet(input_size, hidden_size, output_size).to(device)
    model.load_state_dict(model_state)
    model.eval()
    bot_name = "Sam"
    print("let's chat: type 'quit' to exit")
    context = {}
    while True:
        sentence = input('You: ')
        if sentence == "quit":
            break

        print(f"{bot_name} {chatbot(sentence, data, model, intents, context=context)[1]}")
        
            
                  




# chat()
    # X = bag_of_words(sentence, all_words)
    # X = X.reshape(1, X.shape[0])
    # X = torch.from_numpy(X)

    # output = model(X)
    # print("OUTPUT: ", output)
    # _, predicted = torch.max(output, dim=1)
    # tag = tags[predicted.item()]
    # print("PREDICTED: ", predicted, " ", tag)
    # probs = torch.softmax(output, dim=1)
    # print("PROBS: ", probs)
    # prob = probs[0][predicted.item()]
    # valid_probs = [ p for p in probs.detach().numpy()[0]  if p > 0]
    # print(valid_probs)
    # print("PROB: ", prob.item())
    # if prob.item() > 0.35:
    #     for intent in intents["intents"]:
    #         if tag == intent["tag"]:
    #             print(f"{bot_name}: {random.choice(intent['responses'])}")
    # else:
    #     print(f"{bot_name}: I do not understand ... ")