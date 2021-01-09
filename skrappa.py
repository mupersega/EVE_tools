import os
import queue
from datetime import datetime

import numpy as np
import pandas as pd
import pyperclip

import cfg
from my_funcs import step_show as ss


class Skrappa:
	"""Scan all current market orders in region and see if they are listed below repro value."""

	def __init__(self, buy_region, buy_from, sell_region, sell_to, ores_only: bool, percent, isk):
		self.buy_region = buy_region
		self.buy_from = buy_from
		self.buy_from_hub_id = cfg.regions[buy_region]['hub id']
		self.sell_region = sell_region
		self.sell_to = sell_to
		self.sell_to_hub_id = cfg.regions[sell_region]['hub id']
		self.ores_only = ores_only

		self.sales_tax = .035
		self.ore_efficiency = .632
		self.mod_efficiency = .54
		self.min_percent_return = percent
		self.min_isk_difference = isk

		self.materials = pd.read_csv('data/invTypeMaterials.csv')
		self.invTypes = pd.read_csv('data/invTypes.csv')
		self.all_buy_region_orders = pd.read_csv(f'local_data/{buy_region.lower()}_orders.csv')
		self.all_sell_region_orders = pd.read_csv(f'local_data/{sell_region.lower()}_orders.csv')
		self.sell_orders = None
		self.buy_orders = None
		self.q = queue.Queue()
		self.fails = 0
		self.step = 1

		self.material_values = {}
		self.processed_item_values = {}
		self.opportunities = {}

	def setup(self):
		self.step += 1

		# filter buy and sell orders by hub/region
		self.sell_orders = self.all_buy_region_orders[
			(self.all_buy_region_orders['is_buy_order'] == False)]
		if self.buy_from == 'hub':
			self.sell_orders = self.sell_orders[
				(self.sell_orders['location_id'] == self.buy_from_hub_id) &
				(self.sell_orders.type_id.isin(list(self.materials['typeID'].unique())))]

		self.buy_orders = self.all_sell_region_orders[
			(self.all_sell_region_orders['is_buy_order'] == True)]
		if self.sell_to == 'hub':
			self.buy_orders = self.buy_orders[
				(self.buy_orders['location_id'] == self.sell_to_hub_id)]

		# filter invTypes and set idx
		self.invTypes = self.invTypes[['typeID', 'typeName', 'portionSize', 'marketGroupID']]
		self.invTypes.set_index('typeID', inplace=True)

	def prepare_breakdown_materials(self):
		self.step += 1
		breakdown_mats = self.materials['materialTypeID']
		breakdown_mats = breakdown_mats.unique()
		# filter buy orders to only breakdown materials
		self.buy_orders = self.buy_orders[
			self.buy_orders.type_id.isin(list(breakdown_mats))]
		# for each unique breakdown material find its current max buy value
		for material_id in breakdown_mats:
			# from all current buy orders find those that match the type id of this material
			buys_list = self.buy_orders[(self.buy_orders['type_id'] == material_id)]
			# get the current max buy from _____
			max_buy = buys_list['price'].max()
			# append to dict the id and its current max buy
			self.material_values[material_id] = max_buy

	def populate_piv_dict(self):
		self.step += 1
		# set efficiency
		if self.ores_only:
			efficiency = self.ore_efficiency
		else:
			efficiency = self.mod_efficiency
		# find reprocess value of every unique typeID being SOLD
		for typeID in self.sell_orders['type_id'].unique():
			self.get_id_piv(typeID, efficiency)

	def get_id_piv(self, type_id, efficiency):
		type_reprocessed_value = 0
		ti = type_id
		ef = efficiency
		# pass types that haven't got enough information
		try:
			type_name = self.invTypes.loc[ti][0]
			portion = self.invTypes.loc[ti][1]
			group_id = int(self.invTypes.loc[ti][2])
		except:
			self.fails += 1
			return

		# pass if looking for ores and this type not ore
		if self.ores_only:
			if group_id not in cfg.repro_ore_filter_ids:
				return

		# get list of materials that this type breaks down into
		breakdown_materials = self.materials[(self.materials['typeID'] == ti)]
		repro_info = []
		for m in breakdown_materials.values:
			m_info = {}
			material_id = m[1]
			repro_qty = np.floor((m[2] * ef) / portion)
			material_current_buy = self.material_values[material_id]
			mat_name = self.invTypes.loc[material_id][0]
			# add this material element's value to overall repro value
			repro_value = material_current_buy * repro_qty
			m_info['name'] = mat_name
			m_info['qty'] = repro_qty
			m_info['value'] = repro_value
			repro_info.append(m_info)
			# add this materials value to the value of the parent type
			if repro_value > 0:
				type_reprocessed_value += repro_value

		exp = int(type_reprocessed_value * (1 - self.sales_tax) * (1 - self.sales_tax))
		self.processed_item_values[type_name] = {}
		self.processed_item_values[type_name]['info'] = repro_info
		self.processed_item_values[type_name]['expected'] = exp

	def get_final_opportunities(self):
		self.step += 1
		# for every sell order check if it will reprocess for more than its sell price
		for i in self.sell_orders.values:
			ti = i[9]
			vol = i[10]
			try:
				type_name = self.invTypes.loc[ti][0]
				group_id = int(self.invTypes.loc[ti][2])
				# filter anything that is not ore if ores only
				if self.ores_only:
					if group_id not in cfg.repro_ore_filter_ids:
						pass
				else:
					if type_name in self.processed_item_values.keys():
						price = i[6]
						expected = self.processed_item_values[type_name]['expected']
						undervalue_percentage = (expected - price) / price * 100
						if undervalue_percentage > self.min_percent_return and expected > self.min_isk_difference:
							if type_name not in self.opportunities.keys():
								self.opportunities[type_name] = {'volume': vol, 'buy below': price, 'returning': expected}
							elif type_name in self.opportunities.keys():
								self.opportunities[type_name]['volume'] += vol
								if self.opportunities[type_name]['buy below'] < price:
									self.opportunities[type_name]['buy below'] = price
					else:
						pass
			except:
				self.fails += 1
				pass

	def prep_final_opportunities(self):
		self.step += 1
		open('local_data/latest_scrap.txt', 'w+')
		with open('local_data/latest_scrap.txt', 'a') as text_file:
			paste_string = ""
			for i in sorted(self.opportunities.keys()):
				text_file.write(
					f'{self.opportunities[i]["volume"]} {i.upper()} below {self.opportunities[i]["buy below"]}\n')
				paste_string += i + '\n'
			pyperclip.copy(paste_string)
		os.startfile('local_data\latest_scrap.txt')

	def main(self):
		start_time = datetime.now()
		ss(self.step, "PREPARING files and data frames")
		self.setup()
		ss(self.step, "POPULATING breakdown material values")
		self.prepare_breakdown_materials()
		ss(self.step, "GETTING type processed values")
		self.populate_piv_dict()
		ss(self.step, "SEARCHING for reprocessing opportunities")
		self.get_final_opportunities()
		ss(self.step, "PREPARING final opportunities information")
		self.prep_final_opportunities()
		ss(self.step, "OPERATION COMPLETE", True)
		print(f'\nFAILS:{self.fails}')
		print(f'Finished in {datetime.now() - start_time}')

		# print(self.processed_item_values["Gravimetric Sensor Cluster"])




