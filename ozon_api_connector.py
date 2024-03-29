from pprint import pprint
import psycopg2 as psy
from threading import Thread
import requests
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import os

import time

errors_dict = {
    400: "Bad request (probably atribute json)",
    401: "Authorization failed (probably incorrect user id)",
    403: "Forbidden (probably incorrect access-key)",
    405: "Method is not allowed",
    429: "Too many requests"
}

# Tables to handle with:
# account_list, mark_actions, mark_actions_rules_table

# Data should be added into sql_connection
# sql_my_auth_data = (
# db_name: str,
# db_user: str,
# db_password: str,
# db_host: str,
# db_port: str,
# target_session_attrs: str,
# sslmode: str
# )

sql_select_api_clients = """
    SELECT client_id_api, tmp.api_key
    FROM (SELECT DISTINCT(api_key) from account_list) as tmp
    JOIN account_list
    ON tmp.api_key = account_list.api_key
    WHERE mp_id = 1
    GROUP BY tmp.api_key, client_id_api
    ORDER BY api_key DESC
"""


def sql_connection(db_name, db_user, db_password, db_host, db_port, target_session_attrs, sslmode):
    connection = None
    try:
        connection = psy.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            target_session_attrs=target_session_attrs,
            sslmode=sslmode
        )
        print("Connection to PostgreSQL DB successful")
    except psy.OperationalError as error:
        print(f"The error '{error}' occurred")
    return connection


def insert_data(colum_data, f_values_data, connection, table_name):
    if f_values_data != '':
        insert_query = f"insert into {table_name} ({colum_data}) values {f_values_data}"
        point = connection.cursor()
        point.execute(insert_query)
        connection.commit()
        # print(f"record in {table_name} created")


def delete_data(connection, table_name='mark_actions'):
    delete_query = f"""DELETE FROM mark_actions WHERE ctid IN (SELECT ctid FROM (SELECT *, ctid, row_number()
        OVER (PARTITION BY id_product, id_action, client_id_api ORDER BY id DESC) 
        FROM mark_actions)s WHERE row_number >= 2)"""
    point = connection.cursor()
    point.execute(delete_query)
    connection.commit()
    print(f"doubles {table_name} deleted")


def join_data(super_order_data):
    colum_data = ', '.join(super_order_data.columns.to_list())
    vals = []
    for index, r in super_order_data.iterrows():
        row = []
        for x in r:
            row.append(f"'{str(x)}'")
        row_str = ', '.join(row)
        vals.append(row_str)
    f_values_data = []
    for v in vals:
        f_values_data.append(f"({v})")
    f_values_data = ', '.join(f_values_data)
    return colum_data, f_values_data


class OzonConnector:

    def __init__(self, client_id, api_key):
        self.id = client_id
        self.key = api_key
        self.http = 'https://api-seller.ozon.ru/v1'
        self.db_list = []

    def request_params(self, href_end):
        return f'{self.http}{href_end}', {
            'Client-Id': self.id,
            'Api-Key': self.key,
        }, 30

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
                print(f"""Attempt #{attempt_count} failed(Timeout). 
                Next attempt in {self.request_params("/actions")[2]} seconds""")
                time.sleep(self.request_params('/actions')[2] * attempt_count)
            except requests.codes == 429:
                print(f"""Attempt #{attempt_count} failed(429). 
                Next attempt in {self.request_params("/actions")[2]} seconds""")
                time.sleep(self.request_params('/actions')[2] * attempt_count)
            attempt_count += 1

        dict_of_ids = dict()
        if resp.status_code != 200:
            return dict_of_ids, resp.status_code
        else:
            if resp.status_code == 200:
                # print('successful actions request')
                for action in resp.json()['result']:
                    dict_of_ids[action['id']] = action['date_end']
                # print(len(dict_of_ids))
                return dict_of_ids, resp.json()['result']
            elif resp.status_code in errors_dict.keys():
                return errors_dict[resp.status_code]
            else:
                return f'Unknown status ({resp.status_code})'

    def goods_for_action_get(self, actions: dict, connection):
        relation_goods_to_action = dict()
        if actions is None:
            return 'Empty request'
        else:
            for action_id, end_date in actions.items():
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
                        print(f"""Attempt #{attempt_count} failed(Timeout). 
                        Next attempt in {self.request_params("/actions/candidates")[2]} seconds""")
                        time.sleep(self.request_params('/actions/candidates')[2] * attempt_count)
                    except requests.codes == 429:
                        print(f"""Attempt #{attempt_count} failed(429). 
                        Next attempt in {self.request_params("/actions/candidates")[2]} seconds""")
                        time.sleep(self.request_params('/actions/candidates')[2] * attempt_count)
                    attempt_count += 1

                if resp is None:
                    relation_goods_to_action[action_id] = 'NOT RESPONSE (Timeout or 429)'
                else:
                    if resp.status_code == 200:
                        # print(f'successful goods request (action {action_id})')
                        relation_goods_to_action[action_id] = 0
                        total_goods = resp.json()['result']['total']
                        limit = 10000
                        offset = 0
                        final_df = pd.DataFrame()
                        while offset < total_goods:
                            list_of_goods = requests.post(
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
                            flat_unit = dict()
                            for product in list_of_goods:
                                flat_unit['id_product'] = product['id']
                                flat_unit['id_action'] = action_id
                                flat_unit['price'] = round(float(product['price']), 2)
                                flat_unit['action_price'] = round(float(product['action_price']), 2)
                                flat_unit['max_action_price'] = round(float(product['max_action_price']), 2)
                                flat_unit['add_mode'] = product['add_mode']
                                flat_unit['stock'] = product['stock']
                                flat_unit['min_stock'] = product['min_stock']
                                flat_unit['date_end'] = end_date
                                flat_unit['client_id_api'] = self.id
                                df_unit = pd.DataFrame(flat_unit, index=[0])
                                final_df = pd.concat([df_unit, final_df])
                                if len(final_df) > 10000:
                                    insert_data(*join_data(final_df), connection, 'mark_actions')
                                    relation_goods_to_action[action_id] += len(final_df)
                                    final_df = pd.DataFrame()
                        if len(final_df) != 0:
                            insert_data(*join_data(final_df), connection, 'mark_actions')
                        relation_goods_to_action[action_id] += len(final_df)
                        # print('success')

                    elif resp.status_code in errors_dict.keys():
                        relation_goods_to_action[action_id] = 0
                        print(errors_dict[resp.status_code])

                    else:
                        relation_goods_to_action[action_id] = 0
                        print(f'Unknown status ({resp.status_code})')
            # print('')
            return relation_goods_to_action

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
                        timeout=self.request_params('/actions/products')[2]
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
                if resp.status_code == 200:
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
                            timeout=self.request_params('/actions/products')[2]
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


def daily_uploading_to_db(cli_id_api, api_ke, connection):
    # print(f'#{count} process started')
    # start = time.time()
    oz_con = OzonConnector(cli_id_api, api_ke)
    actions_ = oz_con.all_actions_get()
    if len(actions_) == 0:
        print('No available actions')
        return
    oz_con.goods_for_action_get(actions_[0], connection)
    # end = time.time()
    # print(f'#{count} process finished, duration ={end - start}')
    return 'Done'


if __name__ == '__main__':
    load_dotenv(find_dotenv())
    sql_my_auth_data = tuple(os.getenv('sql_my_auth_data').split(','))

    #
    conn = sql_connection(*sql_my_auth_data)
    pointer = conn.cursor()
    pointer.execute(sql_select_api_clients)
    records = pointer.fetchall()
    pprint(records)

    list_of_threads = []
    for client_id_api, api_key in records:
        th = Thread(target=daily_uploading_to_db, args=(client_id_api, api_key, conn))
        list_of_threads.append(th)
        th.start()

    for thread in list_of_threads:
        thread.join()
    delete_data(conn)
