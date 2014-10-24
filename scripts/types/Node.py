class Node:
	# Node id is unique in a tree (discussion page)
	# it is a sequential enumeration of nodes encountered in the depth-first search
	id = None
	level = None
	author = None
	authorString = None
	timestamp = None
	timestampString = None
	text = None
	
	def __init__(self, id, id_global, level, author, authorString, timestamp, timestampString, text):
		self.id = int(id)
		self.id_global = int(id_global)
		self.level = level
		self.author = int(author)
		self.authorString = authorString
		self.timestamp = timestamp
		self.timestampString = timestampString
		self.text = text
		
	def __str__(self):
		string = "id: " + str(self.id) + ", "
		string += "id_global: " + str(self.id_global) + ", "
		string += "level: " + str(self.level) + ", "
		string += "author: " + str(self.author) + ", "
		string += "authorString: " + str(self.authorString) + ", "
		string += "timestamp: " + str(self.timestamp) + ", "
		string += "timestampString: " + str(self.timestampString) + ", "
		if len(self.text) > 40:
			string += "text: " + str(self.text)[0:20] + " [...] " + str(self.text)[-20:]
		else:
			string += "text: " + str(self.text)

		return string.encode('utf-8')
	
