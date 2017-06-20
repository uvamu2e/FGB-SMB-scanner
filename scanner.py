import sys
import cv2
import image_utils
import file_utils


# Read user input
if len(sys.argv) != 2:
	print("Usage: " + sys.argv[0] + " [new_image_filename]")
	exit()
filename = sys.argv[1]

# Get information about bars to be measured
bar_nums_left = []
bar_nums_right = []

bar_type = raw_input("What type of bar are you measuring? Answer smb / fgb: ")
while bar_type != 'smb' and bar_type != 'fgb':
	bar_type = raw_input("What type of bar are you measuring? Answer smb / fgb: ")
bar_is_smb = bar_type == 'smb'

debug_answer = raw_input("Would you like to enter debug mode? Answer (y)es / (n)o: ")
while debug_answer != 'yes' and debug_answer != 'y' and debug_answer != 'no' and debug_answer != 'n':
	debug_answer = raw_input("Would you like to enter debug mode? Answer (y)es / (n)o: ")
if debug_answer == 'yes' or debug_answer == 'y':
	file_utils.debug_mode = True

use_default = ''
delete_files = False

if file_utils.debug_mode:
	# Auto-fill the bar numbers
	use_default = raw_input("Would you like to use default values for the bar numbers? Answer (y)es / (n)o: ")
	while use_default != 'yes' and use_default != 'y' and use_default != 'no' and use_default != 'n':
		use_default = raw_input("Would you like to use default values for the bar numbers? Answer (y)es / (n)o: ")

	# Show images at each stage of the image processing
	show_image_response = raw_input("Would you like to show images at each stage? Answer (y)es / (n)o: ")
	while show_image_response != 'yes' and show_image_response != 'y' and show_image_response != 'no' and show_image_response != 'n':
		show_image_response = raw_input("Would you like to show images at each stage? Answer (y)es / (n)o: ")
	if show_image_response == 'yes' or show_image_response == 'y':
		image_utils.show_images = True

	# Delete the files made in the `testing` directory
	delete_files_response = raw_input("Would you like to delete all files after run? Answer (y)es / (n)o: ")
	while delete_files_response != 'yes' and delete_files_response != 'y' and delete_files_response != 'no' and delete_files_response != 'n':
		delete_files_response = raw_input("Would you like to show images at each stage? Answer (y)es / (n)o: ")
	if delete_files_response == 'yes' or delete_files_response == 'y':
		delete_files = True

# Make the path structure required for the rest of the program to run
file_utils.create_path_structure()

# Auto-fill numbers
if use_default == 'yes' or use_default == 'y':
	for i in range(1, 12):
		bar_nums_left.append(i)
		bar_nums_right.append(i + 11)
# Get bar numbers from user
else:
	print("")
	print("Input the numbers of the bars you want to measure.")
	print("Ensure the laptop screen and the blue buttons on the scanner are facing you.")
	print("Enter a value of -1 for each slot which is not filled")
	print("")
	print("\tLEFT\tRIGHT")
	for i in range(1, 12):
		left_and_right = []
		while len(left_and_right) != 2:
			print "Row " + str(i) + "\t",
			nums = raw_input("")
			left_and_right = nums.split()
			if len(left_and_right) != 2:
				print "Enter one value for each column."
				continue
			try:
				int(left_and_right[0])
				int(left_and_right[1])
			except ValueError:
				print "Ensure that the values entered are integers."
				left_and_right = [-1]
		left = left_and_right[0]
		right = left_and_right[1]
		bar_nums_left.append(int(left))
		bar_nums_right.append(int(right))

# Compile bar numbers into a single list
bars_nums = []
for b in bar_nums_left:
	bars_nums.append(b)
for b in bar_nums_right:
	bars_nums.append(b)

# Attempt to read the image provided by the user
print("Reading image " + filename)
new_image = cv2.imread(filename, cv2.IMREAD_COLOR)
if new_image is not None:
	image_utils.measure_new_image(new_image, bars_nums, bar_is_smb=bar_is_smb)
else:
	print("Image input was not valid. Ensure the correct filename was given.")
	#exit()
exit()

# Delete the `testing` directory if requested
if delete_files:
	file_utils.clean()


