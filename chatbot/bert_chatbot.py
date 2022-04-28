import numpy as np
import pandas as pd
import re
import torch
import random
import torch.nn as nn
from sklearn.preprocessing import LabelEncoder
from transformers import DistilBertTokenizer, DistilBertModel, AutoModel, BertTokenizerFast, RobertaTokenizer, RobertaModel
from torch.utils.data import TensorDataset, DataLoader, RandomSampler
from torchinfo import summary
from transformers import AdamW
from sklearn.utils.class_weight import compute_class_weight
from torch.optim import lr_scheduler
from .nltk_utils import tokenize, stem
from .chatbot_abstract import Chatbot


class BERTChatbot(Chatbot):

    #3 types of transformer models to choose from
    distilbert = "distilbert-base-uncased"
    roberta = "roberta-base"
    bert = "bert-base-uncased"

    def __init__(self, type="distilbert-base-uncased", batch_size=16, max_seq_len=30, epochs=1000):
        # specify GPU
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        #load pretrained model and tokenizer
        self.tokenizer = self.get_tokenizer(type)
        self.bert = self.get_pretrained_model(type)
        
        # Converts the labels into encodings
        self.le = LabelEncoder()

        #define a batch size
        self.batch_size = batch_size
        #Set the maximum sequence length for we can fine-tune this to achieve better results 
        self.max_seq_len = max_seq_len
        # number of training epochs
        self.epochs = epochs
        

    def get_tokenizer(self, type):
        # Load the desired tokenizer
        if type == BERTChatbot.distilbert:
            return DistilBertTokenizer.from_pretrained(BERTChatbot.distilbert)
        elif type == BERTChatbot.roberta:     
            return RobertaTokenizer.from_pretrained(BERTChatbot.distilbert)
        else:
            return BertTokenizerFast.from_pretrained(BERTChatbot.bert)
            




    def get_pretrained_model(self, type):
        # Import the pretrained model
        if type == BERTChatbot.distilbert:
            return DistilBertModel.from_pretrained(BERTChatbot.distilbert)
        elif type == BERTChatbot.roberta:     
            return RobertaModel.from_pretrained(BERTChatbot.distilbert)
        else:
            return AutoModel.from_pretrained(BERTChatbot.bert)

    def get_train_labels_text(self,data):
        tags = []
        xy = []
        
        for intent in data["intents"]:
            tag = intent["tag"]
            tags.append(tag)
            for pattern in intent["patterns"]:
                xy.append((pattern, tag))
        # print(xy)
        df = pd.DataFrame(xy,  columns=['text','label'])
        # print(df.head())

        df['label'] = self.le.fit_transform(df['label'])
        # check class distribution
        df['label'].value_counts(normalize = True)

        # print("\n\nTrain Text:\n",  df["text"])
        # print("\n\nTrain Labels\n",  df["label"])

        return (df["text"], df["label"])

    def get_model_architecture(self, unique_classes):
        # freeze all the parameters. This will prevent updating of model weights during fine-tuning.
        for param in self.bert.parameters():
            param.requires_grad = False

         #this will determine the final output layer in neural net architecture
        model = BERT_Arch(self.bert, len(unique_classes))

        # push the model to GPU if possible
        model = model.to(self.device)
        summary(model)
        return model
        
    def get_dataloader(self, train_text, train_labels):
         # get length of all the messages in the train set
        seq_len = [len(i.split()) for i in train_text]
        print(seq_len)

        # tokenize and encode sequences in the training set
        tokens_train = self.tokenizer(
            train_text.tolist(),
            max_length = self.max_seq_len,
            pad_to_max_length=True,
            truncation=True,
            return_token_type_ids=False
        )

        # for train set
        train_seq = torch.tensor(tokens_train['input_ids'])
        train_mask = torch.tensor(tokens_train['attention_mask'])
        train_y = torch.tensor(train_labels.tolist())

        print(train_y)

        # wrap tensors
        train_data = TensorDataset(train_seq, train_mask, train_y)
        # sampler for sampling the data during training
        train_sampler = RandomSampler(train_data)

        print("BATCH_SIZE: ", self.batch_size)
        # DataLoader for train set
        return DataLoader(train_data, sampler=train_sampler, batch_size=self.batch_size)
        

    def get_weights(self, unique_classes, train_labels):
        #compute the class weights
        class_wts = compute_class_weight(class_weight="balanced", classes=unique_classes, y=train_labels)
        print(class_wts)
        print(len(class_wts))

        #BALANCING THE WEIGHTS WHILE CALCULATING ERROR
        # convert class weights to tensor
        weights= torch.tensor(class_wts,dtype=torch.float)
        weights = weights.to(self.device)
        print(weights)
        print(len(weights))
        return weights

    # function to train the model
    def train_model(self, model, optimizer, dataloader, loss_func):
    
        model.train()
        total_loss = 0
        
        # empty list to save model predictions
        total_preds=[]
        # We can also use learning rate scheduler to achieve better results
        lr_sch = lr_scheduler.StepLR(optimizer, step_size=100, gamma=0.1)

        # iterate over batches
        for step,batch in enumerate(dataloader):
            
            # progress update after every 50 batches.
            if step % 50 == 0 and not step == 0:
                print('  Batch {:>5,}  of  {:>5,}.'.format(step,len(dataloader)))
            # push the batch to gpu
            batch = [r.to(self.device) for r in batch] 
            sent_id, mask, labels = batch
            # get model predictions for the current batch
            preds = model(sent_id, mask)
            # compute the loss between actual and predicted values
            loss = loss_func(preds, labels)
            # add on to the total loss
            total_loss = total_loss + loss.item()
            # backward pass to calculate the gradients
            loss.backward()
            # clip the the gradients to 1.0. It helps in preventing the exploding gradient problem
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            # update parameters
            optimizer.step()
            # clear calculated gradients
            optimizer.zero_grad()
        
            #apply the learning rate which controls how big of a step for an optimizer to reach the minima of the loss function
            lr_sch.step()

            # model predictions are stored on GPU. So, push it to CPU
            preds=preds.detach().cpu().numpy()
            # append the model predictions
            total_preds.append(preds)
        # compute the training loss of the epoch
        avg_loss = total_loss / len(dataloader)
        
        # predictions are in the form of (no. of batches, size of batch, no. of classes).
        # reshape the predictions in form of (number of samples, no. of classes)
        total_preds  = np.concatenate(total_preds, axis=0)
        #returns the loss and predictions
        return avg_loss, total_preds

    #handles the training process
    def train(self, data):
        train_text, train_labels = self.get_train_labels_text(data)
        unique_classes = np.unique(train_labels)
        model = self.get_model_architecture(unique_classes)
        optimizer = AdamW(model.parameters(), lr = 1e-3)
        dataloader = self.get_dataloader(train_text=train_text, train_labels=train_labels)
        weights = self.get_weights(unique_classes=unique_classes, train_labels=train_labels)

        # loss function
        cross_entropy = nn.NLLLoss(weight=weights) 

        # empty lists to store training and validation loss of each epoch
        train_losses=[]


        for epoch in range(self.epochs):    
            print('\n Epoch {:} / {:}'.format(epoch + 1, self.epochs))
            
            #train model
            train_loss, _ = self.train_model(model=model, optimizer=optimizer, dataloader=dataloader, loss_func=cross_entropy)
            
            # append training and validation loss
            train_losses.append(train_loss)
            # it can make your experiment reproducible, similar to set  random seed to all options where there needs a random seed.
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            print(f'\nTraining Loss: {train_loss:.10f}')
    
        data = {
            "model_state": model.state_dict(),
            "num_classes": unique_classes
        }
        FILE = "bertmodel.pth"
        torch.save(data, FILE)
        return

    def get_prediction(self, str, model):
        str = re.sub(r"[^a-zA-Z ]+", "", str)
        test_text = [str]        
        tokens_test_data = self.tokenizer(
            test_text,
            max_length = self.max_seq_len,
            pad_to_max_length=True,
            truncation=True,
            return_token_type_ids=False
        )
        test_seq = torch.tensor(tokens_test_data["input_ids"])
        test_mask = torch.tensor(tokens_test_data["attention_mask"])
        
        preds = None
        with torch.no_grad():
            preds = model(test_seq.to(self.device), test_mask.to(self.device))
        preds = preds.detach().cpu().numpy()
        preds = np.argmax(preds, axis = 1)
        print("Preds 3: ", preds )
        print("Intent Identified: ", self.le.inverse_transform(preds)[0])
        return self.le.inverse_transform(preds)[0]

    def get_response(self, message, data, file): 
        _, train_labels = self.get_train_labels_text(data)
        unique_classes = np.unique(train_labels)

        #Retrieve trained model
        model_state = file["model_state"]
        # unique_classes = file["unique_classes"]
        model = self.get_model_architecture(unique_classes)
        model.load_state_dict(model_state)
        model.eval()

        result = "I do not understand please try again or ask another question ... "
        intent = self.get_prediction(message, model)
        for i in data['intents']: 
            if i["tag"] == intent:
                if not self.check_response(message, ' '.join(i["responses"]).lower()):
                    intent = ""
                else:
                    result = random.choice(i["responses"])
                break
        print("Intent: "+ intent + '\n' + "Response: " + result)
        return (intent, result)

    def chat(self, data, file):
        bot_name="Sam"
        while True:
            sentence = input('You: ')
            if sentence == "quit" or sentence == "q":
                break

            print(f"{bot_name} {self.get_response(sentence, data, file)[1]}")

        return

    def check_response(self, q, r):
        '''
        Determines the validity of the chatbot's response
        '''
        q = tokenize(q)
        print(q)
        ignore_words = ['?', '!', '.', ',', 'are', 'you', 'can', 'and', 'you', 'let', ]
        stemmed_words  = [stem(w) for w in q if w not in ignore_words and len(w) > 2 ] # avoid punctuation or words like I , a , or 
        print(stemmed_words)
        found = [ w for w in stemmed_words if re.search(w, r) != None] #check if the question has words related in the response
        print(found)
        return len(found) > 0


class BERT_Arch(nn.Module):
   def __init__(self, bert, num_classes):      
       super(BERT_Arch, self).__init__()
       self.bert = bert 
      
       # dropout layer
       self.dropout = nn.Dropout(0.2)
      
       # relu activation function
       self.relu =  nn.ReLU()
       # dense layer
       self.fc1 = nn.Linear(768,512)
       self.fc2 = nn.Linear(512,256)
       self.fc3 = nn.Linear(256,num_classes)
       #softmax activation function
       self.softmax = nn.LogSoftmax(dim=1)
    
    #define the forward pass
   def forward(self, sent_id, mask):
      #pass the inputs to the model  
      cls_hs = self.bert(sent_id, attention_mask=mask)[0][:,0]
      
      x = self.fc1(cls_hs)
      x = self.relu(x)
      x = self.dropout(x)
      
      x = self.fc2(x)
      x = self.relu(x)
      x = self.dropout(x)
      # output layer
      x = self.fc3(x)
   
      # apply softmax activation
      x = self.softmax(x)
      return x








