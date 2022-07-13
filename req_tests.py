import requests

BASE = "http://127.0.0.1:5000/"

resp = requests.get(BASE + 'mark_actions_api',
                    data={'client_id_api': '2663',
                          'api_key': '2342'
                          }
                    )
print(resp.text)
