import os
import cv2
import image_utils

debug_mode = False

measure_smb_dir = 'measurements/smb_images'
measure_fgb_dir = 'measurements/fgb_images'
new_images_dir = 'images'
testing_dir_smb = 'testing/smb_images'
testing_dir_fgb = 'testing/fgb_images'


# Writes a compressed JPEG image using the specified level of compression
# quality = 100 == low compression == large file size
# quality = 0 == high compression == small file size
def write_compressed_image_to_file(image, filename, quality):
	cv2.imwrite(filename, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])


# Adjust the measurement coordinate system so that (x, y) = (0, 0) is centered in the left hole
# and so that (x, y) = (x, 0) is centered in the right hole
def modify_measurements(measurements):
	# All measurements in the form: [center_x, center_y, width or radius, height or nothing]
	# Each set of measurements will contain 6 measurements for the 6 measured holes

	# x = 0, y = 0 is defined to be the center of the left most hole
	zero_x = measurements[0][0]
	zero_y = measurements[0][1]

	# y = 0 is defined to lie along the line connected the center of the left most and right most hole
	# transform all of the measurements to these coordinates
	# Throughout, a measurement value of '-' means a measurement could not be made, so ignore these measurements
	if zero_x == '-' or zero_y == '-':
		return
	slope = (measurements[5][1] - zero_y) / (measurements[5][0] - zero_x)
	for measurement in measurements:
		if measurement[0] != '-':
			measurement[0] -= zero_x
		if measurement[1] != '-':
			measurement[1] -= zero_y + slope*measurement[0]
	for measurement in measurements:
		for i in range(len(measurement)):
			if measurement[i] != '-':
				# This provides the conversion between pixels and millimeters
				# mm = Num (pixels) * 25.4 (mm / inch) * 1 / 2400 (pixels per inch)
				measurement[i] *= 25.4 / 2400.


# Print the measurements to the correct file containing all measurements
def print_measurements_to_file(measurements, bar_num, is_smb):
	if is_smb:
		# If we're in debug mode, put everything in a new testing directory
		if debug_mode:
			filename = "testing/smb_measurements.txt"
		else:
			filename = "measurements/smb_measurements.txt"
		if os.path.isfile(filename):
			out_file = open(filename, 'a+')
		else:
			# Make the file and write a header
			out_file = open(filename, 'w+')
			out_file.write(
				"\tLeft Hole\tSquare 1\t\tSquare 2\t\tSquare 3\t\tSquare 4\t\tRight Hole\n")
			out_file.write("Bar Num\t")
			out_file.write("x (mm)\ty (mm)\tradius (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\twidth (mm)\theight (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\twidth (mm)\theight (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\twidth (mm)\theight (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\twidth (mm)\theight (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\twidth (mm)\theight (mm)\tflagged\n")
	else:
		if debug_mode:
			filename = "testing/fgb_measurements.txt"
		else:
			filename = "measurements/fgb_measurements.txt"
		if os.path.isfile(filename):
			out_file = open(filename, 'a+')
		else:
			# Make the file and write a header
			out_file = open(filename, 'w+')
			out_file.write(
				"\tLeft Hole\t\t\t\t\tFiber 1\t\t\t\t\tFiber 2\t\t\t\t\tFiber 3\t\t\t\t\tFiber 4\t\t\t\t\tRight Hole\n")
			out_file.write("Bar Num\t")
			out_file.write("x (mm)\ty (mm)\tradius (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\tradius (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\tradius (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\tradius (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\tradius (mm)\tflagged\t")
			out_file.write("x (mm)\ty (mm)\tradius (mm)\tflagged\n")

	# A value of '-1' for a measurement (aka < 0) means that the measurement didn't work. Flag this one to be ignored
	for measurement in measurements:
		# print measurement
		for i in range(len(measurement)):
			if measurement[i] < 0:
				measurement[i] = '-'

	# Adjust the coordinate system of the measurements
	modify_measurements(measurements)

	# Print out the measurements
	line = str(bar_num) + '\t'
	for measurement in measurements:
		for data in measurement:
			line += str(data) + '\t'
		line += '\t'
	line += '\n'
	try:
		out_file.write(line)
	except:
		print "Printing to " + filename + " failed. Ensure this file isn't open anywhere else. Exiting."
		exit()


# Print a list of passed bar and hole images. Places images in a directory which follows the format
# measurements/smb_images/smb_bar_number/*.jpg
# measurements/fgb_images/fgb_bar_number/*.jpg
def print_images_to_file(list_of_images, bar_num, is_smb):
	# Construct the correct path to the bar images
	if debug_mode:
		dir_path = "testing/"
	else:
		dir_path = "measurements/"
	if is_smb:
		dir_path += "smb_images/smb_"
	else:
		dir_path += "fgb_images/fgb_"
	dir_path_bar = dir_path + str(bar_num)

	# If the path to the bar folder doesn't exist, make it
	if not os.path.exists(dir_path_bar):
		os.makedirs(dir_path_bar)
	else:
		bar_type = 'smb' if is_smb else 'fgb'
		print("WARNING: A " + bar_type + ' with bar number ' + str(bar_num) + ' was already measured.')
		# Find a folder name which hasn't been made yet
		j = 0
		while os.path.exists(dir_path_bar):
			dir_path_bar = dir_path + str(bar_num) + "_" + str(j)
			j += 1
		# If we're printing out a whole bar image, then make a new folder as this must be a new duplicate bar
		os.makedirs(dir_path_bar)
		# Otherwise, we're printing a hole image, meaning it belongs in the most recently made duplicate folder
	filename = dir_path_bar + "/bar_" + str(bar_num) + ".jpg"
	write_compressed_image_to_file(list_of_images[0], filename, 50)
	for i in range(1, len(list_of_images)):
		filename = dir_path_bar + "/hole_" + str(i) + ".jpg"
		write_compressed_image_to_file(list_of_images[i], filename, 50)


# Create the required path structure for this program
def create_path_structure():
	dirs = [measure_smb_dir, measure_fgb_dir, new_images_dir]
	if debug_mode:
		dirs.append(testing_dir_fgb)
		dirs.append(testing_dir_smb)
	for directory in dirs:
		if not os.path.isdir(directory):
			print "Making directory " + directory
			os.makedirs(directory)


# Delete the `testing` folder and everything inside it
def clean():
	if os.path.isdir("testing"):
		for root, dirs, files in os.walk("testing", topdown=False):
			for name in files:
				os.remove(os.path.join(root, name))
			for name in dirs:
				os.rmdir(os.path.join(root, name))
		os.rmdir("testing")
