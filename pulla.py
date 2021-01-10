import csv
import queue
import threading
from my_funcs import *
import requests

import cfg



class Pulla:
	def __init__(self, lookup_regions):
		self.regions = lookup_regions
		self.step = 0
		self.step_loop = 0
		self.final_step = len(self.regions) * 3
		self.data_path = 'local_data/'
		self.final_write = {}
		self.q = queue.Queue()

	def get_regions_threaded(self):
		for region in self.regions:
			self.step = 0
			self.step += 1
			step_show(self.step, f'QUERYING for {region.title()} market orders')
			step_display(self.step + self.step_loop * 3, self.final_step)
			# build a name for the file from the region specified and clear/create.
			stem = f'https://esi.evetech.net/latest/markets/{cfg.regions[region]["region id"]}/orders/?'
			file_name = f'{region}_orders.csv'
			file = self.data_path + file_name
			threads = []
			for i in range(cfg.regions[region]['pages']):
				x = threading.Thread(target=self.query, args=(stem, i,))
				threads.append(x)
			for tt in threads:
				tt.start()
			for tt in threads:
				tt.join()
			while not self.q.empty():
				resp = self.q.get()
				self.final_write[f'page_{resp[0]}'] = resp[1]
			self.step += 1
			step_show(self.step, f'RECEIVED {len(self.final_write.keys())} pages')
			step_display(self.step + self.step_loop * 3, self.final_step)
			self.write_csv(file)

	def query(self, stem, page):
		params = {'datasource': 'tranquility', 'order_type': 'all', "page": page}
		response = requests.get(stem, params=params)
		# print(response.url)
		# print(response.status_code)
		if response.status_code == 200:
			json_response = response.json()
			# final_write[f'page_{page}'] = new_page
			self.q.put([page, json_response])
			# print(f'page_{page}')
		else:
			return

	def write_csv(self, file_name):
		# open a csv file of same name
		self.step += 1
		step_show(self.step, f'WRITING to csv')
		step_display(self.step + self.step_loop * 3, self.final_step)
		new_csv = open(f'{file_name}', 'w+', newline='')
		csv_writer = csv.writer(new_csv)
		count = 0
		for page in self.final_write:
			for row in self.final_write[page]:
				if count == 0:
					header = row.keys()
					csv_writer.writerow(header)
					count += 1
				else:
					csv_writer.writerow(row.values())
		self.final_write.clear()
		self.step_loop += 1

	def main(self):
		self.get_regions_threaded()

