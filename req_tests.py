import requests

BASE = "http://127.0.0.1:5000/"

# resp = requests.put(BASE + "mark_actions_api", params={"api_id": "2663", "client_id": 2, "rule": "{'key': 'value'}"})
# print(resp.text)

resp = requests.post(BASE + "mark_actions_api", params={"api_id": "2663", "client_id": 2})
print(resp.json())
