
def step_show(step, info, complete=False):
	step_string = ""
	for i in range(step):
		step_string += "- "
	step_string += info
	if complete:
		for i in range(step):
			step_string += " -"
	print(step_string)