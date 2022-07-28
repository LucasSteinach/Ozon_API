import requests
from pprint import pprint

BASE = "http://127.0.0.1:5000/"


class RuleHandler:
    def __init__(self, rule: dict):
        self.rule_id = rule['id']
        self.discount = rule['rule_description']['discount']
        self.client_id = rule['client_id']

    def get_available_products(self, api_id):
        resp = requests.get(BASE + "mark_actions_api", params={"api_id": api_id})
        list_of_products = resp.json()['data']
        return list_of_products


if __name__ == "__main__":
    # resp = requests.put(BASE + "mark_actions_api", params={
    #     "api_id": "2663",
    #     "client_id": 2,
    #     "rule": "{'discount': '5'}"
    # })
    # print(resp.text)

    # resp = requests.post(BASE + "mark_actions_api", params={"api_id": "2663", "client_id": 2})
    # print(resp.json())

    resp = requests.get(BASE + "mark_actions_api", params={"api_id": "2663"})
    pprint(resp.json()['data'])
