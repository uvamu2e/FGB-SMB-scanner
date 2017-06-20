import cv2
from class_defs import rect
import numpy as np
from file_utils import print_measurements_to_file
from file_utils import print_images_to_file

show_images = False

# These are a list of rectangles which tell the program where to crop inside the full scan in order to find each of the bars
bar_rect_list = []
for i in range(11):
	bar_rect_list.append(rect(550, 850 + 2510*i, 9250, 1570))
for i in range(11):
	bar_rect_list.append(rect(10750, 850 + 2510*i, 9250, 1530))

# These are a list of rectangles which tell the program where to crop inside each bar image to find each hole
hole_rect_list = []
#hole_rect_list.append(rect(230, 500, 590, 620))
#hole_rect_list.append(rect(880, 550, 440, 540))
#hole_rect_list.append(rect(3380, 550, 440, 540))
#hole_rect_list.append(rect(5580, 550, 440, 540))
#hole_rect_list.append(rect(8080, 550, 440, 540))
#hole_rect_list.append(rect(8420, 450, 700, 700))

hole_rect_list.append(rect(180, 480, 590, 620))
hole_rect_list.append(rect(780, 500, 440, 540))
hole_rect_list.append(rect(3280, 500, 440, 540))
hole_rect_list.append(rect(5480, 500, 440, 540))
hole_rect_list.append(rect(7980, 500, 440, 540))
hole_rect_list.append(rect(8350, 400, 700, 700))


# Show an image in a new window
def show_image(image, title):
	cv2.imshow(title, image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()


# Measures a new scan fully
def measure_new_image(new_image, bar_nums, bar_is_smb=True):
	# Crop the bars out of the full image
	bar_images = get_bars(new_image)
	# Create a list of bars with problems
	problem_bars = []

	# Measure each bar individually
	for bar, bar_num in zip(bar_images, bar_nums):
		# Skip bars where the user entered -1
		if bar_num == -1:
			continue
		print("Measuring bar " + str(bar_num))

		# Show the croped bar
		if show_images:
			show_image(cv2.resize(bar, (int(bar.shape[1]/10), int(bar.shape[0]/10))), "Bar")

		# Create a list of images to print, starting with the bar image
		images_to_print = [bar]

		# Get the holes from the whole bar image
		if bar_is_smb:
			holes = get_holes(bar)
		else:
			holes = get_holes_fgb(bar)

		# Create a list of measurements
		measurements = []
		i = 0
		if bar_is_smb:
			# Measure each hole. For an SMB, the farthest left hole is a circle, and the rest are squares
			for hole, crop in holes:
				if i == 0:
					measurement, drawn_img = measure_circle(hole, crop.x(), crop.y(), hole_type='smb')
				else:
					measurement, drawn_img = measure_square(hole, crop.x(), crop.y())
				measurements.append(measurement)
				images_to_print.append(drawn_img)
				i += 1
		else:
			# Measure each hole. For a FGB, the farthest left and right holes are dark circles and the inner ones
			# are small fiber holes. Each of these require different parameters to measure the circles
			for hole, crop in holes:
				if i == 0 or i == 5:
					measurement, drawn_img = measure_circle(hole, crop.x(), crop.y(), hole_type='dark')
				else:
					measurement, drawn_img = measure_circle(hole, crop.x(), crop.y(), hole_type='fiber')
				measurements.append(measurement)
				images_to_print.append(drawn_img)
				i += 1

		# Add all of the problems bars to the list to print out later
		for hole_num in range(len(measurements)):
			if -1 in measurements[hole_num]:
				problem_bars.append("[Bar " + str(bar_num) + " Hole " + str(hole_num) + "]")

		# Print the gathered images of the bar and its holes to disk
		print_images_to_file(images_to_print, bar_num, bar_is_smb)
		# Print the gathered measurements of the holes to a file
		print_measurements_to_file(measurements, bar_num, is_smb=bar_is_smb)

	# Print out information about which bars and holes had issues
	if len(problem_bars) > 0:
		print("There was a problem with the bars")
		for b in problem_bars:
			print(str(b))


# Checks if an x, y pixel value is out of the bounds of an image
def is_out_of_bounds(x, y, width, height):
	return x < 0 or y < 0 or x >= width or y >= height


# This function tries to find a better bounding box around a hole of interest
def get_good_crop_rect(image):
	# Apply a gaussian blur filter to the image
	blurred = cv2.GaussianBlur(image, (5, 5), 3, None, 3)
	# Use the canny edge detector to find edges in the image
	edge = cv2.Canny(blurred, 50, 300)

	if show_images:
		show_image(edge, "Canny edge image")

	# Dilate the edges to make them wider, possibly connecting unconnected contours of the hole
	kernel = np.ones((9, 9), np.uint8)
	edge = cv2.dilate(edge, kernel, iterations=1)

	if show_images:
		show_image(edge, "Dilated edge image")

	# Find contours (areas of connected white pixels) in the edge image
	(_, contours, _) = cv2.findContours(edge, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	if contours is not None:
		# Sort the contours by area
		contours = sorted(contours, key=cv2.contourArea, reverse=True)[:1]
		draw_img = image.copy()
		# Draw the contours onto the image
		cv2.drawContours(draw_img, contours, 0, (0, 255, 0), 4)
		# Show the image with contours
		if show_images:
			show_image(draw_img, "Hole with best contours")
		# Draw a bounding box around the largest contour and return that box as a rectangle
		(x, y, w, h) = cv2.boundingRect(contours[0])
		ret_rect = rect(x - 10, y - 10, w + 20, h + 20)
		return ret_rect
	else:
		return None


# Get the holes from a bar image by cropping them out, then finding a better cropped image using the get_good_crop_rect function
# Return a list of hole images and their cropping rectangles
def get_holes(image):
	holes = []
	for crop in hole_rect_list:
		# Crop the image
		candidate_hole = image[crop.y():crop.y() + crop.height(), crop.x():crop.x() + crop.width()]

		if show_images:
			show_image(candidate_hole, "Hole image")

		# Find a better cropped image
		better_rect = get_good_crop_rect(candidate_hole)
		if better_rect is not None:
			# Crop the image again
			candidate_hole = image[crop.y() + better_rect.y():crop.y() + better_rect.y() + better_rect.height(), crop.x() + better_rect.x():crop.x() + better_rect.x() + better_rect.width()]

			if show_images:
				show_image(candidate_hole, "Hole image cropped with contours")

			crop = rect(crop.x() + better_rect.x(), crop.y() + better_rect.y(), better_rect.width(), better_rect.height())

		holes.append((candidate_hole, crop))
	return holes


# Get the holes from a bar image by cropping them out
# Return a list of hole images and their cropping rectangles
# It was found that for the FGB holes, finding contours that surrounding the entire hole did not consistently work
def get_holes_fgb(image):
	holes = []
	for crop in hole_rect_list:
		# Crop the image
		candidate_hole = image[crop.y():crop.y() + crop.height(), crop.x():crop.x() + crop.width()]
		holes.append((candidate_hole, crop))
	return holes


# Crop each of the individual bars out of an image
# Return a list of 22 bar images
def get_bars(image):
	bars = []
	for crop in bar_rect_list:
		bars.append(image[crop.y():crop.y() + crop.height(), crop.x():crop.x() + crop.width()])
	return bars


# Measure a circle
# Return the x and y coordinate of the center of the square and the circle's radius
# Uses the Hough Circle Transform to find circles in an image
def measure_circle(img, x_offset, y_offset, hole_type=None):
	# Set an array of parameters based on the hole type
	# The parameters are:
	#   min_rad_search = the minimum radius to find circles for in the search
	#   max_rad_search = the maximum radius to find circles for in the search
	#   min_rad = the minimum radius to use when considering found circles
	#   max_Rad = the minimum radius to use when considering found circles
	#   canny_thresh = the higher threshold to use in the canny edge detection algorithm

	if hole_type is None:
		print "Must pass a hole type to 'measure_circle'. Exiting..."
		exit()
	elif hole_type == 'smb':
		min_rad_search = 225
		max_rad_search = 255
		min_rad = 225
		max_rad = 255
		canny_thresh = 175
	elif hole_type == 'dark':
		min_rad_search = 225
                max_rad_search = 255
		#max_rad_search = 213
		min_rad = 225
		max_rad = 255
		#max_rad = 212
		canny_thresh = 25
		#canny_thresh = 50
	elif hole_type == 'fiber':
		min_rad_search = 70
		max_rad_search = 80
		min_rad = 70
		max_rad = 80
		canny_thresh = 50
	else:
		print "Did not pass a good hole type to 'measure_circle'. Pass either 'smb', 'dark', or 'fiber'"
		exit()

	# Blur the image using a Gaussian filter
	blurred = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 2, None, 2)

	circles = None
	# Scan through various values of the hough circle threshold to find circles in an image
	# A smaller threshold value will find more circles
	for circle_thresh in range(25, 9, -1):
		# Use the Hough Circle Transform to find circles in an image
		circles = cv2.HoughCircles(image=blurred, method=cv2.HOUGH_GRADIENT, dp=1,
									minDist=3, minRadius=min_rad_search, maxRadius=max_rad_search,
									param1=canny_thresh, param2=circle_thresh)

		# If more than 5 circles were found and more than 2 of those lie within our required range, stop searching for circles
		if circles is not None:
			if len(circles[0]) > 5:
			# Find circles within the range we are looking for
				good_circles = [circles[0][j] for j in range(len(circles[0])) if (min_rad < circles[0][j][2] < max_rad)]
				if len(good_circles) > 2:
					# print "Found", len(good_circles), "circles"
					break

	if circles is not None:
		# Find circles within the range we are looking for
		good_circles = [circles[0][j] for j in range(len(circles[0])) if (min_rad < circles[0][j][2] < max_rad)]
		if len(good_circles) > 0:
			# Among the circles in our good range, average their center coordinates and radii
			center_x = sum([circle[0] for circle in good_circles]) / len(good_circles)
			center_y = sum([circle[1] for circle in good_circles]) / len(good_circles)
			radius = sum([circle[2] for circle in good_circles]) / len(good_circles)
		else:
			# If no good circles were found, return a bad measurements
			return [-1, -1, -1], img.copy()

		# Draw the averaged circle on the orginial image and return that
		return_img = img.copy()
		cv2.circle(return_img, (int(center_x), int(center_y)), int(radius), (0, 255, 0), 2)

		if show_images:
			show_image(return_img, "Hole with circle")

		return [center_x + x_offset, center_y + y_offset, radius], return_img
	else:
		# If no circles were found, return a bad measurement
		return [-1, -1, -1], img.copy()


# Measure a square
# Return the x and y coordinate of the center of the square and the square's width and heigh
# Performs a search from the center of the square outward finding minimum distance edges
# To make a minimum-enclosed rectangle inside the square in the image
def measure_square(img, x_offset, y_offset):
	# Blur the image with a Gaussian filter
	blurred = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (3, 3), 3, None, 3)
	# Use the Canny edge detector to find edges in the image
	edge = cv2.Canny(blurred, 100, 200)

	# Get the width and height of the image of interest
	height, width = edge.shape

	# Start in the center of the image
	x = height / 2
	y = width / 2

	# Set search limits to the left right, top and bottom
	left_lim = int(x - 25)
	right_lim = int(x + 25)
	top_lim = int(y - 25)
	bottom_lim = int(y + 25)

	max_left = 0
	max_top = 0
	min_bot = 1000
	min_right = 1000

	# Search in a range of x values for the bottom edge of the square
	for pixel_x in range(left_lim, right_lim):
		pixel_y = int(y)
		while edge[pixel_y, pixel_x] != 255:
			pixel_y += 1
			if is_out_of_bounds(pixel_x, pixel_y, width, height):
				break
		if pixel_y < min_bot and abs(pixel_y - y) > 20:
			min_bot = pixel_y

	# Search in a range of x values for the top edge of the square
	for pixel_x in range(left_lim, right_lim):
		pixel_y = int(y)
		while edge[pixel_y, pixel_x] != 255:
			pixel_y -= 1
			if is_out_of_bounds(pixel_x, pixel_y, width, height):
				break
		if pixel_y > max_top and abs(pixel_y - y) > 20:
			max_top = pixel_y

	# Search in a range of y values for the right edge of the square
	for pixel_y in range(top_lim, bottom_lim):
		pixel_x = int(x)
		#while edge[pixel_y, pixel_x] != 265:
		while edge[pixel_y, pixel_x] != 255:
			pixel_x += 1
			if is_out_of_bounds(pixel_x, pixel_y, width, height):
				break
		if pixel_x < min_right and abs(pixel_x - x) > 20:
			min_right = pixel_x

	# Search in a range of x values for the left edge of the square
	for pixel_y in range(top_lim, bottom_lim):
		pixel_x = int(x)
		while edge[pixel_y, pixel_x] != 255:
			pixel_x -= 1
			if is_out_of_bounds(pixel_x, pixel_y, width, height):
				break
		if pixel_x > max_left and abs(pixel_x - x) > 20:
			max_left = pixel_x

	# Draw the found rectangle on the image and return it
	return_img = img.copy()
	cv2.rectangle(return_img, (max_left, max_top), (min_right, min_bot), (0, 255, 0))

	if show_images:
		show_image(return_img, "Rectangle")

	# Find the center of the found rectangle and its width and height and return it as a measurement
	center_x = (min_right + max_left)/2.
	center_y = (min_bot + max_top)/2.
	width = min_right - max_left
	height = min_bot - max_top

	return [center_x + x_offset, center_y + y_offset, width, height], return_img
