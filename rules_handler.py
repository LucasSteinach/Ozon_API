import requests
from pprint import pprint
from ozon_api_connector import OzonConnector, sql_connection, sql_my_auth_data, sql_select_api_clients
from threading import Thread

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


def rule_execute(ap_id, ap_ke, cli_id=2):
    rules_list = requests.post(BASE + "mark_actions_api", params={"api_id": ap_id,
                                                                  "client_id": cli_id}).json()['rules']
    if len(rules_list) == 0:
        return 'No rules to handle'
    oz_con = OzonConnector(ap_id, ap_ke)
    for rule_ in rules_list:
        rule_handler = RuleHandler(rule_)
        products_to_add = rule_handler.get_available_products()

        if len(products_to_add) == 0:
            continue
        for action_id, products in products_to_add.items():
            oz_con.goods_to_action_add(action_id, products)


if __name__ == "__main__":
    conn = sql_connection(*sql_my_auth_data)
    pointer = conn.cursor()
    pointer.execute(sql_select_api_clients)
    records = pointer.fetchall()
    pprint(records)

    list_of_threads = []

    for api_id, api_key in records:
        th = Thread(target=rule_execute, args=(api_id, api_key))
        list_of_threads.append(th)
        th.start()

    for thread in list_of_threads:
        thread.join()
