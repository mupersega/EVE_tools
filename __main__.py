
import pulla as api
import flippa
import skrappa


#### problem with sell to locations!!!
if __name__ == '__main__':

	pull = True
	flip = False
	scrap = False

	# pull info
	pull_regions = ['heimatar', 'metropolis']
	# flip info
	flip_regions = ['heimatar', 'domain']
	flip_update_regions = True
	# scrap info
	buy_from_region = 'sinq laison'
	buy_from = 'hub'
	sell_to_region = 'sinq laison'
	sell_to = 'hub'
	isk_threshold = 1000
	percent_return = 10
	ores_only = False
	update_regions = True

	if pull:
		for i in pull_regions:
			api.get_regions_threaded(i)

	if scrap:
		scrap_regions = [buy_from_region, sell_to_region]
		if update_regions:
			for i in set(scrap_regions):
				api.get_regions_threaded(i)
		new_scrap = skrappa.Skrappa(
			buy_from_region, buy_from, sell_to_region, sell_to, ores_only, percent_return, isk_threshold)
		new_scrap.main()

	if flip:
		if flip_update_regions:
			for i in set(flip_regions):
				api.get_regions_threaded(i)
		new_flip = flippa.Flippa(flip_regions)
		new_flip.main()
