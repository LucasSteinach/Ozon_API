from pprint import pprint

import requests


class OzonConnector:

	def __init__(self, client_id, api_key):
		self.id = client_id
		self.key = api_key
		self.http = 'https://api-seller.ozon.ru/v1'

	def all_actions_get(self):
		resp = requests.get(
			f'{self.http}/actions',
			headers={
				'Client-Id': self.id,
				'Api-Key': self.key
					}
							)
		# pprint(resp.json())
		# list_of_actions = []
		# for action in resp.json()['result']:
		# 	list_of_actions.append(
		# 		{'action_type': action['action_type'],
        #           'date_end': action['date_end'],
        #           'date_start': action['date_start'],
        #           'id': action['id'],
        #           'title': action['title'],
		# 		  }
		# 	)
		return resp.json()['result']

	def all_goods_for_action_get(self, action_id):
		resp = requests.post(
			f'{self.http}/actions/candidates',
			headers={
				'Client-Id': self.id,
				'Api-Key': self.key
			},
			json={
				'action_id': action_id,
				'limit': 100,
				'offset': 0
			}
		)
		return resp.json()['result']['products']

	def conditions_for_actions_get(self):
		pass

	def goods_to_action_add(self, action_id, product_id, action_price):
		resp = requests.post(
			f'{self.http}/actions/products/activate',
			headers={
				'Client-Id': self.id,
				'Api-Key': self.key
			},
			json={
				'action_id': action_id,
				'products': {
					'action_price': action_price,
		            'product_id': product_id
				}
			}
		)
		return resp.json()

	def goods_from_action_remove(self, action_id, product_id):
		resp = requests.post(
			f'{self.http}/actions/products/deactivate',
			headers={
				'Client-Id': self.id,
				'Api-Key': self.key
			},
			json={
				'action_id': action_id,
				'product_ids': [
					product_id
				]
			}
		)
		return 'Done'


Client_Id = ''
Api_Key = ''
OC = OzonConnector(Client_Id, Api_Key)
pprint(OC.all_actions_get())
print('---------------')
pprint(OC.all_goods_for_action_get(201871))
