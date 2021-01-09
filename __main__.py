
import pulla
import flippa
import skrappa


if __name__ == '__main__':

	pull = False

	flip = True
	flip_update_regions = True

	scrap = False
	scrap_update_regions = True

	# pull info
	pull_regions = ['domain', 'heimatar']
	# flip info
	flip_regions = ['domain', 'heimatar']
	# scrap info
	buy_from_region = 'heimatar'
	buy_from = 'hub'
	sell_to_region = 'heimatar'
	sell_to = 'hub'
	isk_threshold = 1000
	percent_return = 10
	ores_only = False

	if pull:
		for i in pull_regions:
			pulla.get_regions_threaded(i)

	if scrap:
		scrap_regions = [buy_from_region, sell_to_region]
		if scrap_update_regions:
			for i in set(scrap_regions):
				pulla.get_regions_threaded(i)
		new_scrap = skrappa.Skrappa(
			buy_from_region, buy_from, sell_to_region, sell_to, ores_only, percent_return, isk_threshold)
		new_scrap.main()

	if flip:
		if flip_update_regions:
			for i in set(flip_regions):
				pulla.get_regions_threaded(i)
		new_flip = flippa.Flippa(flip_regions)
		new_flip.main()
