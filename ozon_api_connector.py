from pprint import pprint

import requests

import time

errors_dict = {
    400: "Bad request (probably atribute json)",
    401: "Authorization failed (probably incorrect user id)",
    403: "Forbidden (probably incorrect access-key)",
    405: "Method not allowed",
    429: "Too many requests"
}


class OzonConnector:

    def __init__(self, client_id, api_key):
        self.id = client_id
        self.key = api_key
        self.http = 'https://api-seller.ozon.ru/v1'

    def request_params(self, href_end):
        return f'{self.http}{href_end}', {
            'Client-Id': self.id,
            'Api-Key': self.key,
        }, 4

    def all_actions_get(self):
        resp = None
        attempt_count = 1
        while resp is None and attempt_count < 10:
            try:
                resp = requests.get(
                    self.request_params('/actions')[0],
                    headers=self.request_params('/actions')[1],
                    timeout=self.request_params('/actions')[2]
                )
            except requests.Timeout:
                print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                time.sleep(4)
            except requests.codes == 429:
                print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                time.sleep(4)
            attempt_count += 1

        if resp is None:
            return None
        else:
            if int(str(resp)[-5:-2]) == 200:
                list_of_ids = []
                for action in resp.json()['result']:
                    list_of_ids.append(action['id'])
                return list_of_ids, resp.json()['result']
            elif int(str(resp)[-5:-2]) in errors_dict.keys():
                return errors_dict[int(str(resp)[-5:-2])]
            else:
                return f'Unknown status ({int(str(resp)[-5:-2])})'

    def goods_for_action_get(self, actions: list):
        relation_goods_to_action = dict()
        if actions is None:
            return 'Empty request'
        else:
            for action_id in actions:
                resp = None
                attempt_count = 1
                while resp is None and attempt_count < 10:
                    try:
                        resp = requests.post(
                            self.request_params('/actions/candidates')[0],
                            headers=self.request_params('/actions/candidates')[1],
                            json={
                                'action_id': action_id,
                                'limit': 1,
                                'offset': 0
                            },
                            timeout=self.request_params('/actions/candidates')[2]
                        )
                    except requests.Timeout:
                        print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                        time.sleep(4)
                    except requests.codes == 429:
                        print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                        time.sleep(4)
                    attempt_count += 1

                if resp is None:
                    relation_goods_to_action[action_id] = 'NOT RESPONSE (Timeout or 429)'
                else:
                    if int(str(resp)[-5:-2]) == 200:
                        total_goods = resp.json()['result']['total']
                        limit = 100
                        offset = 0
                        list_of_goods = []
                        while len(list_of_goods) < total_goods:
                            list_of_goods += requests.post(
                                self.request_params('/actions/candidates')[0],
                                headers=self.request_params('/actions/candidates')[1],
                                json={
                                    'action_id': action_id,
                                    'limit': limit,
                                    'offset': offset
                                },
                                timeout=self.request_params('/actions/candidates')[2]
                            ).json()['result']['products']
                            offset += limit
                        relation_goods_to_action[action_id] = list_of_goods

                    elif int(str(resp)[-5:-2]) in errors_dict.keys():
                        relation_goods_to_action[action_id] = errors_dict[int(str(resp)[-5:-2])]

                    else:
                        relation_goods_to_action[action_id] = f'Unknown status ({int(str(resp)[-5:-2])})'
            return relation_goods_to_action

    def actions_for_good_get(self, relation: dict):
        list_of_products = []
        temp = dict(relation)
        for action, products in temp.items():
            if type(products) == list:
                for product in products:
                    product[f'{action}_discount_%'] = round(100 * (1 - product['max_action_price'] / product['price']),
                                                            0)
                list_of_products += products
            else:
                continue
        if len(list_of_products) != 0:
            products_ids = list(set([unit['id'] for unit in list_of_products]))
            products_dict = dict.fromkeys(products_ids, {})
            for product in list_of_products:
                if product['id'] in products_dict.keys():
                    products_dict[product['id']].update(product)
            return products_dict
        else:
            return 'Empty list'

    # creates dict {id_action: list_of_products related to this action}
    def active_products(self, action_id):
        result = dict()
        if type(action_id) is not int:
            return 'Incorrect action id'
        else:
            resp = None
            attempt_count = 1
            while resp is None and attempt_count < 10:
                try:
                    resp = requests.post(
                        self.request_params('/actions/products')[0],
                        headers=self.request_params('/actions/products')[1],
                        json={
                            'action_id': action_id,
                            'limit': 1,
                            'offset': 0
                        },
                        timeout=self.request_params('/actions/candidates')[2]
                    )
                except requests.Timeout:
                    print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                    time.sleep(4)
                except requests.codes == 429:
                    print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                    time.sleep(4)
                attempt_count += 1

            if resp is None:
                result.update({'error': 'NOT RESPONSE (Timeout or 429)'})
            else:
                if int(str(resp)[-5:-2]) == 200:
                    total_goods = resp.json()['result']['total']
                    limit = 100
                    offset = 0
                    list_of_products = []
                    while len(list_of_products) < total_goods:
                        list_of_products += requests.post(
                            self.request_params('/actions/products')[0],
                            headers=self.request_params('/actions/products')[1],
                            json={
                                'action_id': action_id,
                                'limit': limit,
                                'offset': offset
                            },
                            timeout=self.request_params('/actions/candidates')[2]
                        ).json()['result']['products']
                        offset += limit
                    result = {action_id: list_of_products}
        return result


    # added list of products(with action price) to one action
    def goods_to_action_add(self, action_id, products):
        report = dict()
        if type(action_id) != int:
            return 'Incorrect action_id'
        elif type(products) != list:
            return '"Products" type must be list of dicts'
        else:
            for product in products:
                resp = None
                attempt_count = 1
                while resp is None and attempt_count < 10:
                    try:
                        resp = requests.post(
                            self.request_params('/actions/products/activate')[0],
                            headers=self.request_params('/actions/products/activate')[1],
                            json={
                                'action_id': action_id,
                                'products': [{'product_id': product['id'],
                                              'action_price': product['max_action_price'],
                                              'stock': product['stock']
                                              }]
                            },
                            timeout=self.request_params('/actions/products/activate')[2]
                        )
                    except requests.Timeout:
                        print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                        time.sleep(4)
                    except requests.codes == 429:
                        print(f'Attempt #{attempt_count} failed. Next attempt in 4 seconds')
                        time.sleep(4)
                    attempt_count += 1
                if resp is None:
                    report.update({product['id']: 'Response failed. (Timeout or 429'})
                elif len(resp.json()['result']['rejected']) != 0:
                    report.update({product['id']: 'rejected'})
                elif len(resp.json()['result']['product_ids']) != 0:
                    report.update({product['id']: 'added'})
                else:
                    report.update({product['id']: 'has already been added'})
            return report

    # creates list of dicts {id_product: list_of_actions this product participates in}
    def log_of_active_products(self):
        actions = self.all_actions_get()[0]
        result = None
        if type(actions) is not list:
            return 'Error by getting list of actions'
        else:
            for action_id in actions:
                active_products = self.active_products(action_id)
                set_of_products_ids = set()
                if type(active_products) is not dict:
                    continue
                else:
                    for product in list(active_products.values())[0]:
                        if type(product) is not dict:
                            continue
                        else:
                            set_of_products_ids.add(product['id'])
                if result is None:
                    result = dict.fromkeys(list(set_of_products_ids), [action_id])
                else:
                    for product_id in list(set_of_products_ids):
                        if product_id in result.keys():
                            result[product_id].append(action_id)
                        else:
                            result.update({product_id: [action_id]})
            return result


    def goods_from_action_remove(self, action_id, product_id: list):
        resp = requests.post(
            self.request_params('/actions/products/deactivate')[0],
            headers=self.request_params('/actions/products/deactivate')[1],
            json={
                'action_id': action_id,
                'product_ids': product_id
            }
        )
        return resp.json()


Client_Id = ''
Api_Key = ''
OC = OzonConnector(Client_Id, Api_Key)

test_added_products = [{'404776_discount_%': 13.0,
                        'action_price': 0,
                        'add_mode': 'NOT_SET',
                        'id': 7346816,
                        'max_action_price': 722.1,
                        'min_stock': 0,
                        'price': 830,
                        'stock': 0
                        },
                       {'404776_discount_%': 13.0,
                        'action_price': 0,
                        'add_mode': 'NOT_SET',
                        'id': 7346818,
                        'max_action_price': 722.1,
                        'min_stock': 0,
                        'price': 830,
                        'stock': 0
                        }
                       ]

test_deleted_products = [7346816, 7346818]
test_action = 404776
current_actions = OC.all_actions_get()
goods_for_action = OC.goods_for_action_get(current_actions[0])
actions_for_good = OC.actions_for_good_get(goods_for_action)
# print('------------------')
# pprint(goods_for_action)
# print('------------------')
# pprint(actions_for_good)
# print('------------------\n\n\n\n------------------')
# pprint(OC.goods_to_action_add(408548, test_added_products))
# OC.goods_to_action_add(test_action, test_added_products)
# print('------------------\n\n\n\n------------------')
# pprint(OC.goods_from_action_remove(408548, [7223549]))
# print('------------------\n\n\n\n------------------')
pprint(OC.active_products(408548))
# print('------------------\n\n\n\n------------------')
pprint(OC.log_of_active_products())
