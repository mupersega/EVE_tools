
def step_show(step, info, complete=False):
	step_string = ""
	for i in range(step):
		step_string += "- "
	step_string += info
	if complete:
		for i in range(step):
			step_string += " -"
	print(step_string)


def step_display(step, final_step):
	total_steps = 15
	percent = int(step / final_step * total_steps)
	display = ""
	for i in range(percent):
		display += "*"
	for i in range(total_steps - len(display)):
		display += "-"
	print(display)