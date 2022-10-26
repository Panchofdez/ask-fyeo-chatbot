# Ask-fyeo-chatbot

This is the TMU first year engineering office chatbot. It answers questions for first year engineering students. The chatbot is created with a 
pytorch deep neural network and it is encapsulated into a flask api. The chatbot stores the FAQ and essential information about each conversation in a postgres database
which is accessed via this api. The chatbot trains on the information from this FAQ.

There are two types of chatbot supported with this app each using different techniques:
- Bag of words model 
- Bert/transformer based model


## Pre-requisites
1. Download and install docker on local machine
2. Git clone repository onto local machine


## Usage

### In Development Environment
- using a database solely for development purposes
- will create/run a docker container for the chatbot and another container for development database (postgres)

Run app for the first time or if there are any new changes
```docker-compose -f docker-compose-dev.yml up --build```

Re-run app
```docker-compose -f docker-compose-dev.yml up```

Stop app
```docker-compose -f docker-compose-dev.yml down```


### Testing production environments on local machine
- if you want to use the database used in production
- will create/run a docker container only for the chatbot

Commands:
Run app for the first time or if there are any new changes
```docker-compose up --build```

Re-run app
```docker-compose up```

Stop app
```docker-compose down```


### Entering docker container and running commands 

```docker exec -it chatbot bash```


There are 5 commands available when inside container:
1. Train model - trains a chatbot model on the FAQ stored in the corresponding database and saves it into a .pth file
```flask train_model```

2. Chat - Allows you to ask questions with the chatbot 
```flask chat```

3. View intents - View the current FAQ used by the chatbot running in the docker container
```flask view_intents```

4. Test model - Test the chatbot on the current FAQ stored in the corresponding database
```flask test_model```

5. Backup FAQ - Backup the contents of the current FAQ to a intents.json file
```flask backup_faq```


### Train model

1. Start docker container 
2. Enter docker container
`docker exec -it chatbot bash`
3. Train model
`flask train_model`
4. Open new terminal tab
5. Find the id of running docker container 
`docker ps`
6. Copy file from docker container to local machine
`docker cp {id}:app/{filename}.pth . `
