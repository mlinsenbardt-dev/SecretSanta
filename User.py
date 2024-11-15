#!/usr/bin/python
class User:
	def __init__(self,first_name,last_name,email):
		self.first_name = first_name
		self.last_name = last_name
		self.email = email
	def display(self):
		out = str(str(self.first_name) + " " + str(self.last_name) + " : " + str(self.email))
		print(out)
		return out
		