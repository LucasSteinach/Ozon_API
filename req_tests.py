import requests

BASE = "http://127.0.0.1:5000/"

resp = requests.get(BASE + 'mark_actions_api/2663')
print(resp.json())
