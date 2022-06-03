from pprint import pprint

import requests

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
				'Api-Key': self.key
		}

	def all_actions_get(self):
		resp = requests.get(
			self.request_params('/actions')[0],
			headers=self.request_params('/actions')[1]
		)

		if int(str(resp)[-5:-2]) == 200:
			list_of_ids = []
			for action in resp.json()['result']:
				list_of_ids.append(action['id'])
			return list_of_ids, resp.json()['result']
		elif int(str(resp)[-5:-2]) in errors_dict.keys():
			return errors_dict[int(str(resp)[-5:-2])]
		else:
			return f'Unknown status ({int(str(resp)[-5:-2])})'

	def all_goods_for_action_get(self, actions: list):
		relation_goods_to_action = dict()
		for action_id in actions:
			resp = requests.post(
				self.request_params('/actions/candidates')[0],
				headers=self.request_params('/actions/candidates')[1],
				json={
					'action_id': action_id,
					'limit': 1,
					'offset': 0
				}
			)
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
						}
					).json()['result']['products']
					offset += limit
					relation_goods_to_action[action_id] = list_of_goods

			elif int(str(resp)[-5:-2]) in errors_dict.keys():
				relation_goods_to_action[action_id] = errors_dict[int(str(resp)[-5:-2])]

			else:
				relation_goods_to_action[action_id] = f'Unknown status ({int(str(resp)[-5:-2])})'
		return relation_goods_to_action

	def conditions_for_actions_get(self):
		pass

	def goods_to_action_add(self, action_id, product_id, action_price):
		resp = requests.post(
			self.request_params('/actions/products/activate')[0],
			headers=self.request_params('/actions/products/activate')[1],
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
			self.request_params('/actions/products/deactivate')[0],
			headers=self.request_params('/actions/products/deactivate')[1],
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
# pprint(OC.all_goods_for_action_get(OC.all_actions_get()[0]))

