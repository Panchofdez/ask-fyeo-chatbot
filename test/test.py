import requests

resp = requests.post('http://localhost:5000/answer', json={'question': 'Where is the FYEO located?'})
print(resp)