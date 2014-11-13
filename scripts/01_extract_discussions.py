
import urllib2
import json
import string
import codecs
import time
import random
import argparse
from xml.sax.saxutils import unescape

parser = argparse.ArgumentParser(description='Extract talk pages associated to one or more Wikipedia articles through the API')
parser.add_argument('-l', action="store", dest="article_list", default="../article_ids_titles.csv", 
					help="""
					A file containing the list of articles to be scraped through Wikipedia API (one article title per line, with id and title separated by tab)
					""")
parser.add_argument('-o', action="store", dest="output_folder", default="../talk_pages/", 
					help="""
					Output folder for storing the talk pages (one file per article)
					""")

args = parser.parse_args()

log_folder = '../logs/'

#query = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=json&titles=%s' #for json
query_xml = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvprop=content&format=xml&titles=%s'
xml_template = '\t<talkpage id="%s" title="%s">\n%s\n\t</talkpage>\n'

import re
archive_MiszaBot_template_re = re.compile(r'\{\{User:MiszaBot/config.*?counter\s+=\s+(\d+)\n.*?\|archive\s+=\s+(.*?)\n', re.DOTALL) #for xml
archive_box_template_re = re.compile(r'\{\{archive.*?\|.*?(\[\[/.*?)\}\}', re.DOTALL) #for xml
link_re = re.compile(r'\[\[([^|]*?)(?:\|.*?)*?\]\]')

xml_metadata_re = re.compile('<page pageid="(.+?)" ns="1" title="(.+?)">', re.DOTALL)
xml_text_re = re.compile('<rev .*? xml:space="preserve">(.*)</rev>', re.DOTALL)
redirectP = re.compile(r'#REDIRECT \[\[(.*)\]\]')

sleep_time = 0

verbose = True
debug = True
debug_more = False

write_log = True
write_error_log = True

if write_log:
	log = codecs.open(log_folder + 'wikitalk_scraper.log', 'w', 'utf-8')
if write_error_log:
	error_log = codecs.open(log_folder + 'wikitalk_scraper_error.log', 'w', 'utf-8')

not_found = []


def get_wikitext_xml(page):
	page = page.replace(" ", "_")
	
	if sleep_time > 0:
		time.sleep(sleep_time + sleep_time * (random.random()))
	
	if debug_more: print 'opening query xml: ' + query_xml % page
		
	try:
		opener = urllib2.build_opener()
		infile = opener.open(query_xml % urllib2.quote(page.decode('utf-8')))
		page = infile.read().decode('utf-8')
	except IOError, e:
		if hasattr(e, 'reason'):
			print 'We failed to reach a server. ' + query_xml % page
			print 'Reason: ', e.reason
		elif hasattr(e, 'code'):
			print 'The server couldn\'t fulfill the request: ' + query_xml % page
			print 'Error code: ', e.code
		if write_error_log: 
			try:
				error_log.write(page + '\t' + 'Error opening url ' + query_xml % page + '\n')	
			except:
				pass
			error_log.flush()
		return -1, '', ''
	
	found = re.search(xml_metadata_re, page)
	if found:
		id = found.group(1)
		title = unescape(found.group(2), {"&apos;": "'", "&quot;": '"', "&amp;": "&", "&#039;": "'"})
		
		if debug_more: print id + ' -> ' + title
		
		found = re.search(xml_text_re, page)
		if found:
			text = found.group(1)
			
			if debug_more: print 'found text: ' + text[0:30] + ' ...'
			
			redirect_match = redirectP.match(text)
			if redirect_match:
				redirected_title = unescape(redirect_match.group(1), {"&apos;": "'", "&quot;": '"', "&amp;": "&", "&#039;": "'"})
				if debug: print '  Found redirect: ' + text 
				if write_log: log.write('\n  Found redirect: ' + text) 
				return  0, redirected_title, text 
						
			else:
				if debug_more: print 'returning %s, %s, %s' % (str(id), title, text[0:20] + ' ...') 
				return id, title, text
	
	if debug_more: print 'returning -1'	
	return -1, '', ''
			

def wiki_discussion_scraper(article_title):
	
	if debug_more: print 'wiki_discussion_scraper: calling get_wikitext_xml(%s)' % article_title
	id, title, wiki_text = get_wikitext_xml(article_title)
	
	#function 'get_wikitext_xml' returns id=0 in case of redirect
	while id == 0: 
		if debug: print '    Following redirect: ' + article_title + ' -> ' + title 
		if write_log: log.write('\n    Following redirect: ' + article_title + ' -> ' + title) 
		temp_title = title
		id, title, wiki_text = get_wikitext_xml(temp_title)
		if id == 0 and title == temp_title: 
			print 'something wrong with redirects: ' + title  
			break
		
	if id <= 0:
		return ''

	xml = '<article id="%s" title=%s>\n' % (id, title)
	
	last_xml = xml_template % (id, title, wiki_text)
	
	# only the current (not archived) talk page	
	counter = 0
	archive_pages = []			

	found = re.search(archive_box_template_re, wiki_text)
	if found:	
		archives_box = re.findall(link_re, found.group(1))
		if debug: print '\tarchive box found: ' + str(archives_box)
		if write_log: log.write('\n\tarchive box found: ' + str(archives_box))
		for a in archives_box:
			archive_pages.append(title + a) 

	archive_links_re = re.compile(r'\[\[(' + title + '/[^|^#]*?)(?:\|.*?)?\]\]')
	found = re.findall(archive_links_re, wiki_text)
	if found:	
		if debug: print '\tarchive links found: ' + str(found)
		if write_log: log.write('\n\tarchive links found: ' + str(found) )
		archive_pages += found
		
	found = re.search(archive_MiszaBot_template_re, wiki_text)
	if found:
		counter, archive = found.group(1), found.group(2)		
		for i in range(1, int(counter) + 1):
			archive_pages.append(archive.replace("%(counter)d", str(i)))
		if debug: print '\tMisznaBot archives found: ' + str(counter) + ' -> ' + archive #str(archive_pages)
		if write_log: log.write('\n\tMisznaBot archives found: ' + str(counter) + ' -> ' + archive) #str(archive_pages)
						
	archive_pattern = '%s/Archive_' % title
	last_i = 0
	i = 1
	while i > last_i:
		last_i = i
		id, title, wiki_text = get_wikitext_xml(archive_pattern + str(i))
		if id > 0:
			if archive_pattern + str(i) not in archive_pages and archive_pattern.replace('_', ' ') + str(i) not in archive_pages:
				archive_pages.append(archive_pattern + str(i))
			else:
				if debug_more: print '\tSkipped repeated archive page: ' + archive_pattern + str(i)
				if write_log: log.write('\n\tSkipped repeated archive page: ' + archive_pattern + str(i) )
			
			i += 1	
	
	if i > 1: 
		if debug: print '\tLooking for "Archive_<n>" pattern, found ' + str(i-1) + ' archives, until: ' + archive_pattern + str(i-1)	
		if write_log: log.write('\n\tLooking for "Archive_<n>" pattern, found ' + str(i-1) + ' archives, until: ' + archive_pattern + str(i-1) )
	else: 
		if write_log: log.write('\n\t\tNot found: ' + archive_pattern + str(i) ) 
	
	n_archives_written = 0
	processed_archives = []
	for a in archive_pages:		
		if a not in processed_archives and string.replace(a, '_', ' ') not in processed_archives:		
			id, title, wiki_text = get_wikitext_xml(a)
			if id > 0:
				xml += xml_template % (id, title, wiki_text)
				n_archives_written += 1
			else:
				if debug: print '     Could not access archive %s' % a
				if write_log: log.write('\n     Could not access archive %s' % a )
				if write_error_log: 
					error_log.write(a + '\t' + 'Could not access archive %s\n' % a )
					error_log.flush()
		processed_archives.append(a)
		processed_archives.append(string.replace(a, '_', ' '))
	
	if verbose or debug: print "   %s: written current talk page and %d archive pages" %(article_title, n_archives_written)	
	xml += 	last_xml	
	xml += "</article>"
	
	return xml

	
def load_id_list_from_file(file_name):
	
	csvP = re.compile(r'(.?\d+)\s(.*)\n')
	
	d = {}
	f = codecs.open(file_name, 'r', 'utf-8')
	
	j = 0
	for line in f:
		if line[0] != '#':
			csvM = csvP.match(line)
			if csvM:
				d[int(csvM.group(1))] = csvM.group(2)
				j += 1
			else:
				print 'problem matching line ' + line
	f.close()		
	print '%d lines	read from file %s' % (j, file_name)
	return d


if __name__ == '__main__':
	
	titles = load_id_list_from_file(args.article_list)  
	for id in sorted(titles):
		if verbose or debug: print '\nProcessing article: ' + str(id) + ' ' + str(titles[id])
		if write_log: 
			try:
				log.write('\n\n' + str(id) + ' ' + str(titles[id]) )
			except:
				log.write('\n\n' + str(id) + ' Exception writing article title')
		t = string.replace(titles[id],' ', '_')

		xml = wiki_discussion_scraper("Talk:" + titles[id] ) #titles[id])
		if xml == '': 
			not_found.append(titles[id])
			if debug: print '   Talk page not found: ' + "Talk:" + titles[id]
			if write_log: 
				try:
					log.write('\n   Talk page not found: ' + "Talk:" + titles[id] )
				except:
					log.write('\n   Talk page not found: ' + str(id) + ' Exception writing article title')
		else: 		
			f_out = codecs.open(args.output_folder + 'article_talk_' + str(id) + '.wikitext', 'w', 'utf-8')		
			f_out.write(xml)
			f_out.close()
		log.flush()	

	print '\nEnd. Not found: %d articles:' % len(not_found)
	for t in not_found: print '  ' + t

	
