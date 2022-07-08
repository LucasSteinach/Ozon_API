import requests

BASE = "http://127.0.0.1:5000/"

resp = requests.get(BASE + 'mark_actions_api/sdfljk/vaao')
print(resp.json())
resp = requests.post(BASE + 'mark_actions_api/sdfljk/vaao')
print(resp.json())
resp = requests.delete(BASE + 'mark_actions_api/sdfljk/vaao')
print(resp.json())
resp = requests.put(BASE + 'mark_actions_api/sdfljk/vaao')
print(resp.json())
