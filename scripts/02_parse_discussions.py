
# basic imports
import time
from datetime import date
import re
import os
import codecs

# network library
import networkx as nx

# import classes
import sys
sys.path.append('types/')
import Node

# import utilities
sys.path.append('utilities/')
import conv

# patterns
import patterns

# parse options and arguments. Note that options -p and -d should be considered as mutually exclusive
from optparse import OptionParser
usage = "usage: %python 02-wikitext2trees.py -p pagelist -d directory\n"

# execution parameters:
debug = False
debugSkipDiscussion = False
debugDate = False
debugUsers = False
debugWrongUser = False
debugRE = False
superdebug = False

#to count minutes and days from January 1st, 2001
time_start = 978307200/60
day_minutes = 86400/60

#separator for output files
sep = '\t'

#True if using DB for user names (not working at the moment)
db = False

#assign ids to all nodes
currentNodeIdGlobal = -1


### VERY IMPORTANT: set it to true if the input files are user talk pages, false otherwise
userTalk = False

skipAnonymous = False
skipUsersOver = 15000000000

#to process only the first N files
onlyFirstN = False
N_max_files = 100

#write output in compct format (all comments in one single file, one comment or structural element per line).
write_compact = False
write_compact_text = True

write_titles = True
write_thread_titles = True

#maximum depth of structural nodes 
#(level 0: article, level 1: talk page, level 2: thread title, level 3: second level thread title, ...)
maxThreadLevels = 10



optparser = OptionParser()
optparser.add_option("-d", "--directory", dest="dir", default="../talk_pages/",
   help="directory containing talk page files")
optparser.add_option("-n", "--name", dest="name", default="",
    help="prefix of output file names")   
(opts, args) = optparser.parse_args()

prefix = opts.name
if prefix != "": prefix += '_'
outFolder = "../discussions/" + prefix
logFolder = '../logs/' + prefix

#inventing the ids of users... 
#reading ids from DB or file not supported in this version
user_map = {}

# global variables:
startTime = time.time()

errorLog = open(logFolder + 'error.log', 'a') 
dateLog = open(logFolder + 'errors-dates.log', 'a')
userLog = open(logFolder + 'errors-users.log', 'a')
archiveLog = open(logFolder + 'archive-index.log', 'a') 
processedFilesLog =  open(logFolder + 'processed-files.log', 'a')


compact_header_fields = ['global_id','parent_global_id','id','parent_id','level','article', 'talk_page','thread','timestamp', 'day','author','parent_author','author_name','parent_author_name', 'date']

text_header_fields = ['text']
	
if write_compact:
	compact_output = open(outFolder + 'discussions.csv', 'w')	
	compact_output.write(sep.join(compact_header_fields) + '\n')
	
if write_compact_text:
	compact_output_text = open(outFolder + 'discussions_text.csv', 'w')	
	compact_output_text.write(sep.join(compact_header_fields + text_header_fields) + '\n' )	

if write_titles:	
	out_titles = open(outFolder + 'talk_titles.csv', 'w')
	out_titles.write(sep.join(['article_id','talk_page_id','talk_page_title']) + '\n')	
if write_thread_titles:
	thread_file = open(outFolder + 'thread_titles.csv', 'w')
	thread_file.write(sep.join(['article_id','talk_page_id','talk_page','thread_id','thread_title']) + '\n')
	
users = {}

id = 0
userName = ''

signedComments = 0

g = None
lastNode = None
currentNodeId = 0
currentLevel = 0

currentThreadGlobal = 0

parentString = ""
userString = ""
timestampString = ""

textString = ""

art_id = 0

discussionId = 0

def main():

	global id
	global signedComments

	global discussionId
	global thread_id
	global talk_id	
		
	errorLog.write('\n* Starting. Time: ' + str(startTime) + '\n')
	
	userLog.write('\n* Starting. Time: ' + str(startTime) + '\n')
	userLog.write('\narticle_id\tuser_name\n')
	
	dateLog.write('\n* Starting. Time: ' + str(startTime) + '\n')
	dateLog.write('\narticle_id\tdate\n')
	
	archiveLog.write('\n* Starting. Time: ' + str(startTime) + '\n')
	archiveLog.write('\narticle_id\tdiscussion_page_title\n')

	inputFolder = opts.dir
	print 'Retrieving list of files in directory: ' + opts.dir
	files = os.listdir(inputFolder)
	totPages = len(files)
	print 'directory: ' + inputFolder + " has " + str(totPages) + ' objects (file or directories)' 

	i = 0
	FileP = re.compile(r'article_talk_(.*?).wikitext')
	UserTalkFileP = re.compile(r'user(.*)talk.wikitext')
				

	SKIP = False
	
	for file in files:
	
		if onlyFirstN and i > N_max_files:
			break

		file = file.strip('\n')
		if debug: print 'Processing file: ' + file
		titleMatched = False
		if not userTalk:
			fileMatch = FileP.match(file)
			if (fileMatch):
				art_id = int(fileMatch.group(1))
				id = art_id
				titleMatched = True
				if debug and not SKIP:
					print 'Article id: ' + str(art_id)

		else:
			userFileMatch = UserTalkFileP.match(file)
			if(userFileMatch):
				uid = userFileMatch.group(1)
				id = uid

				if skipAnonymous:
					if int(id) > skipUsersOver:
						continue
				
				titleMatched = True
				if debug and not SKIP:
					print 'User id: ' + uid	
							
		if titleMatched and not SKIP:			
			init_article() 
			g.graph['artId'] = id
			g.graph['date'] = date.today()
			g.graph['discussions'] = []
			pageFile = inputFolder + file
			if debug:
				print 'pageFile: ' + pageFile

			signedComments = 0

			parse(id, pageFile)
			i += 1
			processedFilesLog.write(str(id) + '\n')
			
			if i % 10000 == 0:
				print str(i) + ' articles processed (' + str(float(i) * 100/totPages) + '%)'
				now = time.time()
				print 'time elapsed: ' + str((now - startTime)/3600) + " hours"
				print 'time left (estimated): ' + str(((now - startTime)/3600)*(totPages-i)/i) + " hours"
				errorLog.write(str(i) + ' articles processed (' + str(float(i) * 100/totPages) + '%)')	
				errorLog.write('time elapsed: ' + str((now - startTime)/3600) + "hours" + '\n')
				errorLog.write('time left (estimated): ' + str(((now - startTime)/3600)*(totPages-i)/i) + "hours" + '\n')	


	if write_compact:
		compact_output.close()
	if write_compact_text:
		compact_output_text.close()

	dateLog.write('\n')
	userLog.write('\n')	
	archiveLog.write('\n')
	processedFilesLog.write('\n')
	dateLog.close()
	userLog.close()	
	errorLog.close()
	archiveLog.close()	
	processedFilesLog.close()
	
	
def init_article():  

	global g
	global lastNode
	global currentNodeId
	global currentNodeIdGlobal
	global currentThreadGlobal
	global discussionId	
		
	global parentString
	global userString
	global timestampString
	
	global textString
	
	g = nx.DiGraph()
	lastNode = None
	currentNodeId = 0
	currentNodeIdGlobal += 1	
	currentThreadGlobal = currentNodeIdGlobal
	discussionId = 0

	parentString = ""
	userString = ""
	timestampString = ""
	textString = ""
	

def parse(id, pageFile):
	
	global currentThreadGlobal
	global discussionId

	if userTalk:
		userName = conv.id2username(user_map, int(id))
		if debug: print 'Start analyzing discussion for user: ' + userName + ' (' + str(id) + ')'

	text = ""
	unsigned = False
	firstThreadFound = False
	firstPostFound = False
	table= False
	skipLine = False
	bracesOpened = 0
	bracesClosed = 0
	
	skipDiscussion = False
	
	page = open(pageFile, 'r')
	#line = page.readline()
	line = None
	while line != '':
		line = page.readline()
		
		articleTag = patterns.articleTagP.match(line)
		if articleTag:
			art_id = articleTag.group(1)
			art_title = articleTag.group(2)
			currentThreadGlobal = addNode(-maxThreadLevels, 0, 0, '<' + art_title + '>')
		
		else:		
			if not firstThreadFound:
				if bracesOpened > bracesClosed:
					skipLine = True
				elif line.startswith("{{"):
					skipLine = True
				bracesOpened += line.count("{{")
				bracesClosed += line.count("}}")
				if skipLine:
					if debug: print "Skipping line: " + line
					skipLine = False			
					continue

			if line != '</root>\n':
				discussionTitleMatched = False
				startDiscussionTag = patterns.startDiscussionP.match(line)
				endDiscussionTag = patterns.endDiscussionP.match(line)
				if startDiscussionTag:
					discussionTitleMatched=True
				else:
					startDiscussionTag = patterns.startDiscussionNoTitleP.match(line)
				
				if startDiscussionTag:
					firstThreadFound = False
					firstPostFound = False
					bracesOpened = 0
					bracesClosed = 0
					level = -maxThreadLevels + 1
					discussionId = startDiscussionTag.group(1)
	
					if debug: print "Discussion page: " + discussionId
					if discussionTitleMatched:
						discussionPageTitle = startDiscussionTag.group(2).replace(' ','_')
						if debug: print "Discussion title: " + discussionPageTitle	
						text = discussionPageTitle
						if patterns.archiveIndexP.match(discussionPageTitle):
							skipDiscussion = True
							if debugSkipDiscussion:
								print 'skipping discussion page ' + discussionPageTitle
							errorLog.write('Skipping: ' + discussionPageTitle + ' (' + str(id) + ')\n')
							archiveLog.write(str(id) + "\t" + discussionPageTitle + "\n")
						else:
							skipDiscussion = False
							if write_titles:
								out_titles.write('\t'.join([str(id), str(discussionId), discussionPageTitle]) + '\n')
					else:
						#this should not happen
						#discussionPageTitle = ''
						if userTalk:
							text = conv.id2username(user_map, int(id)) 
						else:
							text = str(id)
						### retrieve username from user id, and create title "User talk:usename"
						
					#to make discussion page title recognizable in the "content" file 	
					text = '<' + text + '>'	
					currentThreadGlobal = addNode(level, 0, 0, text)
					text = ""
					currentLevel = 0

				elif endDiscussionTag:
					skipDiscussion = False
					if unsigned and (firstThreadFound or firstPostFound) and text != '':	
						addNode(level, -1, -1, text)
					unsigned = False
					text = ""
				
				elif not skipDiscussion:
					if patterns.startTableP.match(line):
						table = True
						if debugRE:
							print "  *** startTable matched: " + line
							raw_input('press enter')
						
					elif patterns.endTableP.match(line):
						table = False
						if debugRE:
							print "  *** endTable matched: " + line	
							raw_input('press enter')										
				
					else:
						threadTitle = patterns.threadP.match(line)
						if threadTitle and not table:
							if unsigned and (firstThreadFound or firstPostFound) and text != '':
								# save the preceding post (recognized as unsigned)
								addNode(level, -1, -1, text)
							unsigned = False
							firstThreadFound = True	
							text = ""
							threadLevel = len(threadTitle.group(2))
							level = threadLevel - maxThreadLevels
							title = threadTitle.group(1)
							currentLevel = 0
						
							currentThreadGlobal = addNode(level, 0, 0, title)
							
							if write_thread_titles:
								thread_file.write('\t'.join(map(str,[id, discussionId, discussionPageTitle,currentThreadGlobal,title])) + '\n')
							
						else:		
							oldSeparator = patterns.oldSeparatorP.match(line)
							if oldSeparator:	
								if debugRE:
									print "Separator: " + line		
								if unsigned:
									if debug:
										print "Adding unsigned comment: " + text + "\n"
									addNode(level, -1, -1, text)
									unsigned = False
							elif patterns.emptyLineP.match(line) or line =='\n':
								continue	
							else:	
								# if this condition is satisfied, a new post is starting
								#(ie: last line was not unsigned text, so we are not inside of a message with no signature)
								if not unsigned:
									text = ""
									m = patterns.startPostP.match(line)
									level = len(m.group(2))
									currentLevel = level
									if debugRE:
										print "\n*startPost* pattern matched: level = " + str(level) + "\n" + line
										raw_input('Press enter to continue')		
									firstLine = m.group(1)
									if firstLine != '':
										line = firstLine + '\n'
								
								#last line was text with no signature, so we could be in the middle of a message
								else:
									# if line starts with ":", a new post is starting, even if last line was not signed 
									newPost = patterns.startPostStrictP.match(line)
									if newPost:
										firstPostFound = True
										if debugRE:
											print "\n*startPostStrict* pattern matched: level = " + str(level) + " (current: " + str(currentLevel) + ")\n" + line
											raw_input('Press enter to continue')		
										level = len(newPost.group(2))
										#keep the current line for the next step: looking for a signature inside it.
										#(no need to assign line the value of group(1), containing the entire line, without '\n' in the end)
										#line = newPost.group(1)
										if level != currentLevel:		
											if unsigned:
												if debug:
													print "\nAdding unsigned comment of level " + str(currentLevel) + " -- found new comment of level " + str(level) + ")\n"
													raw_input('Press enter to continue')								
												# save the preceding post (recognized as unsigned)
												addNode(level, -1, -1, text)
											text = ""
										currentLevel = level
								
								#look for a signature in the current line, with many possible conventions
								#(actually 9 patterns are matched)
								line = patterns.manyBlanksP.sub(' ', line)
								if superdebug:
									print 'testing signatureDateP'
								endPost = patterns.signatureDateP.match(line)
								if endPost:	
									firstPostFound = True
									text += endPost.group(1)
									user = endPost.group(2)
									date = endPost.group(3)
									if debugDate:
										print 'signatureDate, date: ' + str(date) 
									if debugRE:
										print "\n*signatureDate* pattern matched: \n" + line
										raw_input('Press enter to continue')
									addNode(level, user, date, text)
									unsigned = False
									text = ""			
								else:
									if superdebug:
										print 'testing autoSignatureDateP'
									endPost = patterns.autoSignatureDateP.match(line)
									if endPost:
										firstPostFound = True
										text += endPost.group(1)
										user = endPost.group(2)
										date = endPost.group(3)
										if debugDate:
											print 'autoSignatureDate, date: ' + str(date) 
										if debugRE:
											print "\n*autoSignatureDate* pattern matched:\n" + line
											raw_input('Press enter to continue')
										addNode(level, user, date, text)
										unsigned = False
										text = ""
									else:
										if superdebug:
											print 'testing dateDignatureDateP'
										endPost = patterns.dateSignatureP.match(line)
										if endPost:
											firstPostFound = True
											text += endPost.group(1)
											user = endPost.group(3)
											date = endPost.group(2)
											if debugDate:
												print 'dateSignature, date: ' + str(date) 
											if debugRE:
												print "\n*dateSignature* pattern matched:\n" + line
												raw_input('Press enter to continue')
											addNode(level, user, date, text)
											unsigned = False
											text = ""
										else: 
											if superdebug:
												print 'testing autoDignatureDateP'
											endPost = patterns.autoDateSignatureP.match(line)
											if endPost:
												firstPostFound = True
												text += endPost.group(1)
												user = endPost.group(3)
												date = endPost.group(2)
												if debugDate:
													print 'autoDateSignature, date: ' + str(date) 
												if debugRE:
													print "\n*autoDateSignature* pattern matched:\n" + line
													raw_input('Press enter to continue')
												addNode(level, user, date, text)
												unsigned = False
												text = ""
											else: 
												if superdebug:
													print 'testing autoDignatureSomethingP'
												endPost = patterns.autoSignatureSomethingP.match(line)
												if endPost:
													firstPostFound = True
													text += endPost.group(1)
													user = endPost.group(2)
													date = endPost.group(3)
													if debugDate:
														print 'autoSignatureSomething, date: ' + str(date) 
													if debugRE:
														print "\n*autoSignatureSomething* pattern matched:\n" + line
														raw_input('Press enter to continue')
													addNode(level, user, date, text)
													unsigned = False
													text = ""
												else: 	
													if superdebug:
														print 'testing autoSignatureP'
													endPost = patterns.autoSignatureP.match(line)
													if endPost:
														firstPostFound = True
														text += endPost.group(1)
														user = endPost.group(2)
														date = -1
														if debugRE:
															print "\n*autoSignature* pattern matched:\n" + line
															raw_input('Press enter to continue')
														addNode(level, user, date, text)
														unsigned = False
														text = ""
													else: 			
														if superdebug:
															print 'testing signatureP'																																				
														endPost = patterns.signatureP.match(line)
														if endPost:
															firstPostFound = True
															if debugRE:
																print "\n*signature* pattern matched:\n" + line
																raw_input('Press enter to continue')							
															text += endPost.group(1)
															user = endPost.group(2)
															date = -1
															addNode(level, user, date, text)
															unsigned = False
															text = ""	
														else:
															if superdebug:
																print 'testing dateP'
															endPost = patterns.dateP.match(line)
															if endPost and not userTalk:
																firstPostFound = True
																text += endPost.group(1)
																user = -1
																date = endPost.group(2)
																if debugDate:
																	print 'date, date: ' + str(date)
																if debugRE:
																	print "\n*date* pattern matched:\n" + line		
																	raw_input('Press enter to continue')									
																addNode(level, user, date, text)
																unsigned = False
																text = ""				
															else:
																if superdebug:
																	print 'testing badSignatureP'
																endPost = patterns.badSignatureP.match(line)
																if endPost:
																	text += endPost.group(1)
																	if text != '':
																		firstPostFound = True
																		user = -1
																		date = -1
																		if debugRE:
																			print "\n*badSignature* pattern matched:\n" + line	
																			raw_input('Press enter to continue')
																		addNode(level, user, date, text)
																		unsigned = False
																		text = ""
																	
																#no signature was found, so just add text to the current comment,
																#and continue looking for its signature in the following lines 	
																else:
																	text += line
																	unsigned = True
																	if debugRE:
																		print "\nNo pattern matched:\n" + line	
																		raw_input('Press enter to continue')										
	page.close()
	
	if debug:
		print 'found %s nodes' % str(g.number_of_nodes())
	
	return 1
	

def addNode(level, user, date, text):

	global users
	global currentNodeId
	global currentNodeIdGlobal
	global lastNode
	global g
	
	global parentString
	global userString
	global timestampString
	global textString
	
	global id
	global userName
	
	global signedComments
	
	if debugDate:
		print 'debug date, add node: ' + str(date)
	
	currentNodeId += 1
	currentNodeIdGlobal += 1

	# by default a node has no parent (0)
	parentId = 0
	parentIdGlobal = 0
			
	
	if type(user) == str:
		userS = user
		
		if users.has_key(userS):
			user = users[userS]
		else:
			user = conv.user2int(user_map, user)
			users[userS] = user
			if user < 0:
				userLog.write(str(id) + '\t' + str(userS) + '\n' )
				if userTalk:
					errorLog.write("Usertalk: " + str(id) + '\tProblems with user: ' + str(userS) + '\n')
				else:
					errorLog.write("Page: " + str(id) + '\tProblems with user: ' + str(userS) + '\n')			
	else:
		userS = str(user)
		
	if type(date) == str:
		dateS = date
		date = conv.date2int(date)
		if date < 0:
			dateLog.write(str(id) + '\t' + str(dateS) + '\n' )
			if userTalk:
				errorLog.write('Problems with date: ' + str(dateS) + ' (' + "usertalk: " + str(id) + ')\n')
			else:
				errorLog.write('Problems with date: ' + str(dateS) + ' (' + "page: " + str(id) + ')\n')			
	else:
		dateS = str(date)
		
	if user > 0:
		signedComments += 1
	
	node = Node.Node(currentNodeId, currentNodeIdGlobal, level, user, userS, date, dateS, text)
	g.add_node(node)

	
	if debug:
		print 'Adding: ' + str(node)


	parentAuthor = 0
	parentAuthorString = ''		
	parentId = 0
	parentIdGlobal = 0	

	if level > -maxThreadLevels:
		predecessorNode = lastNode
		while predecessorNode != None and node.level <= predecessorNode.level:
			
			# it is assumed that every node has one and only one
			# predecessor since it is a tree
			predecessorNode = g.predecessors(predecessorNode)[0]

		g.add_edge(predecessorNode, node)

		if predecessorNode != None:
			parentId = predecessorNode.id
			parentIdGlobal = predecessorNode.id_global	
			parentAuthor = int(predecessorNode.author)
			parentAuthorString = predecessorNode.authorString
							
	else:
		# keeps track of roots for each tree in the graph
		g.graph['discussions'].append(node)	
		
	if debug:
		print 'Parent: ' + str(parentId)
		
	if write_compact or write_compact_text:
		compact_node = [str(currentNodeIdGlobal), str(parentIdGlobal), str(currentNodeId), str(parentId), str(level),  str(id), str(discussionId), str(currentThreadGlobal), str(date), str(timestamp2day(date)), str(node.author), str(parentAuthor), node.authorString, parentAuthorString, dateS] 
		if write_compact:
			write_compact_node(compact_node)
		if write_compact_text:
			write_compact_node_text(compact_node, text)	
		
	if debug:
		raw_input('press enter')
	lastNode = node
	return currentNodeIdGlobal 

def write_compact_node(compact_node):
	compact_output.write(sep.join(compact_node) + '\n')

def write_compact_node_text(compact_node, text):
	compact_output_text.write(sep.join(compact_node + [flatten(text)]) + '\n')


def load_list_from_file(file_name):
	d = {}
	f = open(file_name, 'r')
	j = 0
	for line in f:
		j += 1
		#uncomment next line to skip first (header) line
		#if j == 1: continue
		d[line.stripline('\n')] = 1
	return d
	
def timestamp2day(ts):
	if ts > 0:
		return (ts - time_start)/day_minutes
	else:
		return ts	
	
def flatten(text):
	return text.replace('\n', '   <LF>   ').replace('\t', '   <TAB>   ')


if __name__ == '__main__':	
	main()
	
	end = time.time()
	print 'job completed after: ' + str(end - startTime)
