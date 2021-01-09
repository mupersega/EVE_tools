import pandas as pd
import os
import time

import cfg
from my_funcs import step_show as ss

pd.set_option('display.max_rows', 10)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class Flippa:
	def __init__(self, lookup_regions: list):
		self.regions = lookup_regions
		self.step = 0
		self.x_percent = .90

		self.invTypes = pd.read_csv('data/invTypes.csv')
		self.invTypes = self.invTypes[['typeID', 'typeName', 'portionSize', 'marketGroupID']]
		self.invTypes.set_index('typeID', inplace=True)

		self.market_orders = {}
		self.opportunities = []
		self.purchase_orders = {}

	def setup(self):
		self.step += 1
		# import and load each market orders dict entry(buys-sells), also filter by location id(hub) at this stage.
		for region in self.regions:
			hub_id = cfg.regions[region]['hub id']
			# import this i orders
			region_orders = pd.read_csv(f'local_data/{region}_orders.csv')
			print(f'{region}:{region_orders.shape}')
			# filter by hub
			print(f'- FILTERING: {region.title()} to hub only')
			region_orders = region_orders.query(f'location_id == {hub_id}')
			self.market_orders[region] = {}
			print(f'- - LOADING: {region.title()} buy orders')
			self.market_orders[region]['buy_orders'] = region_orders.query('is_buy_order == True')
			print(f'- - - LOADING: {region.title()} sell orders')
			self.market_orders[region]['sell_orders'] = region_orders.query('is_buy_order == False')
			print(f'- - - - {region.upper()} COMPLETE')
		time.sleep(5)


	def load_all_mins_and_maxes(self):
		self.step += 1
		for region in self.regions:
			self.load_mins_and_maxes(region)

	def load_mins_and_maxes(self, region):
		r = region
		print(f'- POPULATING {r.title()} min_sells')
		self.market_orders[r]['min_sells'] = self.get_min_sells(r)
		print(f'- - POPULATING {r.title()} max_buys')
		self.market_orders[r]['max_buys'] = self.get_max_buys(r)
		print(f'- - - {r.upper()}: mins/maxes populated')

	def get_min_sells(self, region):
		# for every unique typeid for sale find its cheapest sell value and append to min_sells
		min_sells = []
		sell_orders = self.market_orders[region]['sell_orders']
		for type_id in sell_orders['type_id'].unique():
			cheapest = sell_orders[sell_orders['type_id'] == type_id]['price'].min()
			min_sells.append({'type_id': type_id, 'price': cheapest})
		return min_sells

	def get_max_buys(self, region):
		max_buys = []
		buy_orders = self.market_orders[region]['buy_orders']
		for type_id in buy_orders['type_id'].unique():
			max = buy_orders[buy_orders['type_id'] == type_id]['price'].max()
			max_buys.append({'type_id': type_id, 'price': max})
		return max_buys

	def find_opportunities(self):
		self.step += 1
		# for every region check other regions to see if sells are less than buys
		# if a buy is less than a sell: log the id for further analysis
		mmin_sell = {}
		mmax_buys = {}
		# for every region in market orders
		for region in self.market_orders.keys():
			# and for every type in min buy orders
			for entry in self.market_orders[region]['min_sells']:
				type_id = entry['type_id']
				price = entry['price']
				if type_id not in mmin_sell.keys():
					mmin_sell[type_id] = price
					if type_id in mmin_sell.keys():
						if mmin_sell[type_id] < price:
							mmin_sell[type_id] = price
			for entry in self.market_orders[region]['max_buys']:
				type_id = entry['type_id']
				price = entry['price']
				if type_id not in mmax_buys.keys():
					mmax_buys[type_id] = price
					if type_id in mmin_sell.keys():
						if mmax_buys[type_id] > price:
							mmax_buys[type_id] = price
			
			for type_id in mmin_sell.keys():
				sp = mmin_sell[type_id]
				try:
					bp = mmax_buys[type_id]
					if sp * self.x_percent < bp:
						self.opportunities.append(type_id)
				except:
					pass
		print(len(self.opportunities))
		print(self.opportunities)

	def analyse_opportunities(self):
		self.step += 1
		# filter all market orders of anything but opportunities
		for region in self.market_orders.keys():
			sell_orders = self.market_orders[region]['sell_orders']
			buy_orders = self.market_orders[region]['buy_orders']
			sell_orders = sell_orders[sell_orders.type_id.isin(self.opportunities)]
			buy_orders = buy_orders[buy_orders.type_id.isin(self.opportunities)]
			self.market_orders[region]['sell_orders'] = sell_orders
			self.market_orders[region]['buy_orders'] = buy_orders

		# for every region(pr) find sell orders of region and buy orders of other(other) regions
		for pr in self.regions:
			# prep list for load into purchase orders
			self.purchase_orders[pr] = {}
			sell_orders = self.market_orders[pr]['sell_orders']
			reg_buy_orders = []
			r_list = []
			# prep reg orders by dropping all other region buy order dfs in there for loop later
			for other_region in self.regions:
				if other_region == pr:
					pass
				else:
					r_list.append(other_region)
					reg_buy_orders.append(self.market_orders[other_region]['buy_orders'])
			counted_order_ids = []
			for v in sell_orders.values:
				type_id = v[9]
				price = v[6]
				vol = v[10]
				order_id = v[5]
				type_name = self.invTypes.loc[type_id][0]
				r_count = 0
				for df in reg_buy_orders:
					matches = df[df['type_id'] == type_id]
					for match in matches.values:
						m_price = match[6]
						m_vol = match[10]
						m_min_volume = match[4]
						m_order_id = match[5]
						if m_price > price * self.x_percent:
							if type_name not in self.purchase_orders[pr].keys():
								self.purchase_orders[pr][type_name] = {
									'buy_below': price,
									'sell to': r_list[r_count],
									'sell_at': m_price,
									'buy_amt': m_vol,
									'min_volume': m_min_volume,
									'orders': [m_order_id]
								}
								counted_order_ids.append(m_order_id)
							elif type_name in self.purchase_orders[pr].keys():
								if self.purchase_orders[pr][type_name]['buy_below'] < price:
									self.purchase_orders[pr][type_name]['buy_below'] = price
								if self.purchase_orders[pr][type_name]['sell_at'] < m_price:
									self.purchase_orders[pr][type_name]['sell_at'] = m_price
								if m_order_id not in counted_order_ids:
									self.purchase_orders[pr][type_name]['buy_amt'] += m_vol
									counted_order_ids.append(m_order_id)
					r_count += 1

	def present_purchase_orders(self):
		self.step += 1
		if len(self.purchase_orders) < 1:
			ss(self.step, "NO OPPORTUNITIES")
		open('local_data/flip.txt', 'w+')
		with open('local_data/flip.txt', 'a') as text_file:
			for region in sorted(self.purchase_orders.keys()):
				text_file.write(f'\n-<|{region.upper()}|>-\n')
				for item in self.purchase_orders[region].keys():
					dict = self.purchase_orders[region][item]
					sell_to = dict['sell to']
					sell_at = dict['sell_at']
					buy_amt = dict['buy_amt']
					buy_below = dict['buy_below']
					text_file.write(f'{item.title()} \n')
					text_file.write(f'\tBUY |{buy_amt}|@|{buy_below}ISK|\n')
					text_file.write(f'\tSELL |{sell_at}ISK|@|{sell_to.title()}|\n')
		os.startfile(r'local_data\flip.txt')
		# for i in self.purchase_orders.keys():
		# 	print(f'{i}: {self.purchase_orders[i]}')

	def main(self):
		ss(self.step, "PREPARING all region market orders")
		self.setup()
		ss(self.step, "POPULATING cheapest sell and highest buy prices")
		self.load_all_mins_and_maxes()
		ss(self.step, "SEARCHING for arbitrage opportunities")
		self.find_opportunities()
		ss(self.step, f'ANALYZING {len(self.opportunities)} opportunities')
		self.analyse_opportunities()
		ss(self.step, 'PRESENTING flip opportunities')
		self.present_purchase_orders()


























#
# regions = ['heimatar', 'metropolis', 'domain']
# purchase = {
# 	'heimatar': {
# 		'metropolis': {
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			}
# 		},
# 		'domain': {
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			}
# 		}
# 	},
# 	'metropolis': {
# 		'heimatar': {
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			}
# 		},
# 		'domain': {
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			}
# 		}
# 	},
# 	'domain': {
# 		'heimatar': {
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			}
# 		},
# 		'metropolis': {
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			},
# 			'item': {
# 				'buy below': value,
# 				'volume': volume,
# 				'order ids': []
# 			}
# 		}
# 	}
# }