
import pulla
import flippa
import skrappa


if __name__ == '__main__':

	update_all = 1
	pull = 0
	flip = 0
	scrap = 1

	# pull info
	pull_regions = ['heimatar']
	# flip info
	flip_regions = ['domain', 'the forge']
	# scrap info
	buy_from_region = 'the forge'
	buy_from = 'hub'
	sell_to_region = 'the forge'
	sell_to = 'hub'
	isk_threshold = 5000
	percent_return = 10
	ores_only = False

	all_regions = ['heimatar', 'domain', 'the forge', 'metropolis', 'sinq laison']
	# ____PULLA____ #
	if pull:
		if update_all:
			# noinspection PyRedeclaration
			pull_regions = all_regions
			new_pulla = pulla.Pulla(pull_regions)
			new_pulla.main()
	# ___SKRAPPA___ #
	if scrap:
		scrap_regions = [buy_from_region, sell_to_region]
		if update_all:
			new_pulla = pulla.Pulla(set(scrap_regions))
			new_pulla.main()
		new_scrap = skrappa.Skrappa(
			buy_from_region, buy_from, sell_to_region, sell_to, ores_only, percent_return, isk_threshold)
		new_scrap.main()
	# ____FLIPPA____ #
	if flip:
		if update_all:
			flip_regions = all_regions
		new_pulla = pulla.Pulla(flip_regions)
		new_pulla.main()
		new_flip = flippa.Flippa(flip_regions)
		new_flip.main()
