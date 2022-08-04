import requests
from pprint import pprint

BASE = "http://127.0.0.1:5000/"


class RuleHandler:
    def __init__(self, rule: dict):
        self.rule_id = rule['rule_id']
        self.api_id = rule['api_id']
        self.discount = rule['rule_description']['discount']
        self.client_id = rule['client_id']

    def get_available_products(self):
        resp = requests.get(BASE + "mark_actions_api", params={"api_id": self.api_id})
        list_of_products = resp.json()['data']
        res = {}
        for product in list_of_products:
            if product['id_action'] not in res.keys():
                res[product['id_action']] = [product]
            else:
                res[product['id_action']].append(product)
        return res


if __name__ == "__main__":
    pass

    # resp = requests.put(BASE + "mark_actions_api", params={
    #     "api_id": "2663",
    #     "client_id": 2,
    #     "rule": "{'discount': '5'}"
    # })
    # print(resp.text)

    # resp = requests.get(BASE + "mark_actions_api", params={"api_id": "2663"})
    # pprint(resp.json()['data'])
    #
    # rules = requests.post(BASE + "mark_actions_api", params={"api_id": "2663", "client_id": 2}).json()['rules']
    # print(rules)
