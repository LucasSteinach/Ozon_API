import requests
from pprint import pprint
from ozon_api_connector import OzonConnector, join_data, delete_data, insert_data, sql_connection, sql_my_auth_data, \
    errors_dict, sql_select_api_clients

BASE = "http://127.0.0.1:5000/"


class RuleHandler:
    def __init__(self, rule: dict):
        self.rule_id = rule['rule_id']
        self.api_id = rule['api_id']
        self.discount = rule['rule_description']['discount']
        self.client_id = rule['client_id']
        self.base_url = "http://127.0.0.1:5000/"

    def get_available_products(self):
        resp = requests.get(self.base_url + "mark_actions_api", params={"api_id": self.api_id,
                                                                        "discount": self.discount})
        list_of_products = resp.json()['data']
        res = {}
        for product in list_of_products:
            product['action_price'] = product['max_action_price']
            product['product_id'] = product['id']
            if product['id_action'] not in res.keys():
                res[product['id_action']] = [product]
            else:
                res[product['id_action']].append(product)
        return res


def rule_execute(rule, ):
    pass


if __name__ == "__main__":
    conn = sql_connection(*sql_my_auth_data)
    pointer = conn.cursor()
    pointer.execute(sql_select_api_clients)
    records = pointer.fetchall()
    pprint(records)

    # rules = requests.post(BASE + "mark_actions_api", params={"api_id": '2663', "client_id": 2}).json()['rules']
    # # pprint(rules)
    # RH = RuleHandler(rules[0])
    # pprint(RH.get_available_products())

    for api_id, api_key in records:
        rules = requests.post(BASE + "mark_actions_api", params={"api_id": api_id, "client_id": 2}).json()['rules']
        # pprint(rules)
        if len(rules) == 0:
            continue
        OzCon = OzonConnector(api_id, api_key)
        for rule in rules:
            RulHand = RuleHandler(rule)
            products_to_add = RulHand.get_available_products()
            # pprint(products_to_add)
            # print(list(products_to_add.keys()))
            if len(products_to_add) == 0:
                continue
            for action_id, products in products_to_add.items():
                # print(len(products))
                # print(f'action {action_id}. products adding')
                pprint(OzCon.goods_to_action_add(action_id, products))
                # print(f'action {action_id} addition finished.\n\n')
                # pprint(OzCon.active_products(action_id))
                # print(f'active products for action {action_id}\n\n')




