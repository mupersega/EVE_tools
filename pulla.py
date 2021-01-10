import csv
import json
import queue
import threading
import time
import multiprocessing
import concurrent.futures

import requests

import cfg

data_path = 'local_data/'
# request info

final_write = {}
PAGE_COUNT = 1

Q = queue.Queue()


def query(stem, page):
	params = {'datasource': 'tranquility', 'order_type': 'all', "page": page}
	response = requests.get(stem, params=params)
	# print(response.url)
	print(response.status_code)
	if response.status_code == 200:
		json_response = response.json()
		# final_write[f'page_{page}'] = new_page
		Q.put([page, json_response])
		print(f'page_{page}')
	else:
		return


def get_regions_threaded(region):
	# build a name for the file from the region specified and clear/create.
	stem = f'https://esi.evetech.net/latest/markets/{cfg.regions[region]["region id"]}/orders/?'
	file_name = f'{region}_orders.csv'
	file = data_path + file_name
	threads = []
	for i in range(cfg.regions[region]['pages']):
		x = threading.Thread(target=query, args=(stem, i,))
		threads.append(x)
	for tt in threads:
		tt.start()
	for tt in threads:
		tt.join()
	while not Q.empty():
		resp = Q.get()
		print(f'page_')
		final_write[f'page_{resp[0]}'] = resp[1]
		print(f'page{resp[0]}')

	print(f'{region}:{len(final_write.keys())} pages')
	write_csv(final_write, file)


def write_csv(jf_data, file_name):
	# open a csv file of same name
	new_csv = open(f'{file_name}', 'w+', newline='')
	csv_writer = csv.writer(new_csv)
	count = 0
	for page in jf_data:
		for row in jf_data[page]:
			if count == 0:
				header = row.keys()
				csv_writer.writerow(header)
				count += 1
			else:
				csv_writer.writerow(row.values())


