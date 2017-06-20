# A definition of a rectangle for utility
class rect:
	def __init__(self, x, y, width, height):
		self.__x = x
		self.__y = y
		self.__width = width
		self.__height = height

	def x(self):
		return self.__x

	def y(self):
		return self.__y

	def width(self):
		return self.__width

	def height(self):
		return self.__height
