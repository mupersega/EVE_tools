import csv
import json
import queue
import threading
import time

import requests

import cfg

data_path = 'local_data/'
# request info

# params = {
# 	'datasource': 'tranquility',
# 	'order_type': 'all',
# 	'page': 0
# }
final_write = {}
PAGE_COUNT = 1

Q = queue.Queue()


def get_regions_threaded(region):
	# build a name for the file from the region specified and clear/create.
	stem = f'https://esi.evetech.net/latest/markets/{cfg.regions[region]["region id"]}/orders/?'
	file_name = f'{region}_orders.json'
	file = data_path + file_name
	open(file, "w+")
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
		final_write[f'page_{resp[0]}'] = resp[1]
		print(f'page{resp[0]}')
	
	time.sleep(3)

	# write json
	with open(file, "a") as write_file:
		json.dump(final_write, write_file)

	print(f'{region}:{len(final_write.keys())} pages')

	convert_json_to_csv(file)
	print(f'{region.title()} market orders complete.')
	final_write.clear()
	time.sleep(3)


def query(stem, page):
	params = {'datasource': 'tranquility', 'order_type': 'all', "page": page}
	response = requests.get(stem, params=params)
	# print(response.url)
	print(response.status_code)
	if response.status_code == 200:
		json_response = response.json()
		# final_write[f'page_{page}'] = new_page
		Q.put([page, json_response])
	else:
		return


def convert_json_to_csv(json_file):
	# convert json to csv
	file = json_file
	file_name = json_file.split('.')[0]
	# load and assign json to variable
	with open(file) as jf:
		jf_data = json.load(jf)

	# open a csv file of same name
	new_csv = open(f'{file_name}.csv', 'w', newline='')

	# create a csv writer object and assign its file
	csvwriter = csv.writer(new_csv)

	# line counter
	count = 0

	for page in jf_data:
		for row in jf_data[page]:
			if count == 0:
				header = row.keys()
				csvwriter.writerow(header)
				count += 1

			csvwriter.writerow(row.values())
