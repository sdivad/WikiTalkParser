#conversion 02-wikitext2trees.py

debug = False
debugDate = False
debugUsers = False
debugWrongUser = False

# basic imports
import time
from datetime import date
import re
import urllib	
import htmllib

import unicodedata

import sys
sys.path.append('types/')

def date2int(date):
	date = unescapeHTML(date)
	
	p = re.compile(r'(?:,|[.]|[|]|[[]|[]]|th|nd|rd|(&\S+?;)|nbsp;)')
	date = p.sub(' ', date)
	date = date.replace('1st', '1')	
	
	blankP = re.compile(r'\s+')
	date = blankP.sub(' ', date)
	
	try:
		i = int(time.mktime(time.strptime(date, '%H:%M %d %B %Y (%Z)')))
	except ValueError:
		try:
			i = int(time.mktime(time.strptime(date, '%H:%M %d %b %Y (%Z)')))
		except ValueError:
			try:
				i = int(time.mktime(time.strptime(date, '%H:%M %B %d %Y (%Z)')))
			except ValueError:
				try:
					i = int(time.mktime(time.strptime(date, '%H:%M %b %d %Y (%Z)')))
				except ValueError:
					#try:
					#	i = int(time.mktime(time.strptime(date, '%H:%M %d %B %Y')))
					#except ValueError:
					#	try:
					#		i = int(time.mktime(time.strptime(date, '%H:%M %d %b %Y')))
					#	except ValueError:
					#		try:
					#			i = int(time.mktime(time.strptime(date, '%H:%M %B %d %Y')))
					#		except ValueError:
					#			try:
					#				i = int(time.mktime(time.strptime(date, '%H:%M %b %d %Y')))
					#			except ValueError:
					i = -1
					return i

	if debugDate:
		raw_input("[date2int]: " + date + " to " + str(i))
	#date is in seconds; translate it into minutes
	return i/60


 
def user2int(conn, username):
	match = re.match("(\d+)\.(\d+)\.(\d+)\.(\d+)", username)
	if match:
		i = ip2int(match)
		if debugUsers:
			print 'ip: ' + username + ', value: ' + str(i)
		if i < 0:
			print 'bad ip: ' + str(username)
	else:
		i = username2id(conn, username)
		if debugUsers:
			print 'id: ' + username + ', value: ' + str(i)
	
	if debugWrongUser and i == -1:
		raw_input("[user2int], problem with: " + str(username))
	
	if debugUsers:
		raw_input('[user2int]: ' + username + " -> " + str(i))
	
	return i

def ip2int(match) :
        ret = 0
        try:
        	for i in xrange(4) : ret = (ret << 8) + int(match.groups()[i])
        except:
        	ret = -1
        return ret
	
def username2id(conn, user):
	
	id = -1
	if isinstance(conn, dict):
		if user in conn:
			return conn[user]
		else:
			id = len(conn) + 1
			conn[user] = id
			return id	
		try:
			id = conn[user]
		except KeyError:
			id = -1
		return id
		
	#to retrieve user info from a DB
	#~ else: ...	

	c.close()
	return id
	
	
def id2username(conn, id):
	
	c = conn.cursor()
	result = db.executePS(c, 'findUserName', (id,))
	
	for tuple in c:

		if result > 0: # == 1:
			username = c.fetchone()[0]
			c.close()
			return username
		elif result == 0:
			return None
			if debugUsers:
				raw_input('[id2username], problems with user: ' + str(id))
		else:
			return '?'
	
	c.close()
	return None
	
def id2pagename(conn, id, type):
	# id must be a string but now is unusefull to check it
	c = conn.cursor()
	if type == 'article':
		result = db.executePS(c, 'findArticleName', (id,))
	elif type == 'talk':
		result = db.executePS(c, 'findTalkName', (id,))
	if result == 1:
		pagename = c.fetchone()[0]
		c.close()
		return pagename
	
	c.close()
	return '?'

def unescape(s):
	s = unescapeHTML(s)
	s = unescapeHTML(s)
	
	if '%' in s:
		s = urllib.unquote(s)
		
	s = s.replace('_', ' ')
	return s

def unescapeHTML(s):
	if '&' in s:
		p = htmllib.HTMLParser(None)
		p.save_bgn()
		p.feed(s)
		return p.save_end()
	return s
