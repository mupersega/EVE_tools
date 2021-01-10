
import pulla
import flippa
import skrappa


if __name__ == '__main__':

	update_all = True
	# ____PULLA____ #
	pull = 0
	# ____FLIPPA____ #
	flip = 0
	flip_update_regions = 0
	# ___SKRAPPA___ #
	scrap = 1
	scrap_update_regions = 1

	# pull info
	pull_regions = ['heimatar']
	# flip info
	flip_regions = ['domain', 'heimatar']
	# scrap info
	buy_from_region = 'sinq laison'
	buy_from = 'hub'
	sell_to_region = 'sinq laison'
	sell_to = 'hub'
	isk_threshold = 1000
	percent_return = 10
	ores_only = False

	all_regions = ['heimatar', 'domain', 'the forge', 'metropolis', 'sinq laison']

	if pull:
		if update_all:
			# noinspection PyRedeclaration
			pull_regions = all_regions
			new_pulla = pulla.Pulla(pull_regions)
			new_pulla.main()

	if scrap:
		scrap_regions = [buy_from_region, sell_to_region]
		if scrap_update_regions:
			for i in set(scrap_regions):
				new_pulla = pulla.Pulla(scrap_regions)
				new_pulla.main()
		new_scrap = skrappa.Skrappa(
			buy_from_region, buy_from, sell_to_region, sell_to, ores_only, percent_return, isk_threshold)
		new_scrap.main()

	if flip:
		if flip_update_regions:
			if update_all:
				flip_regions = all_regions
			for i in set(flip_regions):
				new_pulla = pulla.Pulla(flip_regions)
				new_pulla.main()
		new_flip = flippa.Flippa(flip_regions)
		new_flip.main()
