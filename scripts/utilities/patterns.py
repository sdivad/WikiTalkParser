# patterns used in 02-wikitext2trees.py

import re

#~ articleTagP = re.compile(r'root id="(.*?)" title="(.*?)"')

#to be changed when the input format will be corrected
articleTagP = re.compile(r'<article id="(.*?)" title=Talk:(.*?)>')
#~ articleTagP = re.compile(r'<article id="(.*?)" title="(.*?)"')

toSkipP = re.compile(r'^\s*(?:(?:\{\{.*?\}\})|(?:\[\[.*?\]\])\s*)+$')
emptyLineP = re.compile(r'^\s+$')

#~ startDiscussionNoTitleP  = re.compile(r'\s*<discussion discussionpage="(.+)">\s*') # title="(.+)"
startDiscussionNoTitleP  = re.compile(r'\s*<talkpage id="(.+)">\s*') # title="(.+)"

#startDiscussionP = re.compile(r'\s*<discussion discussionpage="(.*?)"\s*title=Talk:"(.*?)">\s*') #
#~ startDiscussionP = re.compile(r'\s*<discussion discussionpage="(.*?)"\s*title="(.*?)">\s*') #
startDiscussionP = re.compile(r'\s*<talkpage id="(.*?)"\s*title="(.*?)">\s*') #

#~ endDiscussionP = re.compile(r'\s*</discussion>\n')
endDiscussionP = re.compile(r'\s*</talkpage>\n')

#~ threadP = re.compile(r'((=+)\s*.*?\s*=+)\s*$')
threadP = re.compile(r'((=+)\s*.+?\s*=+)\s*$')

# detects the start of a post
startPostP = re.compile(r'\s*((:*).*)')
startPostStrictP = re.compile(r'\s*((:+).*)')

# components of the following patterns:
textP = r'(.*?)-{0,2}\s*'
htmlP = r'(?:\s*&lt;.*?&gt;\s*)?'
beforeUserP = r'(?:(?:The p|P)receding .*? comment (?:was )?added by\s*)?\s*'
userP = r'.{0,2}\s*\[\[(?:User(?:\s+[tT]alk)?:|Special:Contributions/)\s*(?:\{\{\S*?:)?\s*(?:\|\s*)?\s*(?:[Uu]ser:)?\s*([^]^[^}^{^#^/]*?)\s*(?:/[^]^[]*?)?\s*(?:\|[^]^[]*?)?(?:\}\})?\s*\]\]\s*\S*\s*'
#userP = r'.{0,2}\[\[(?:User(?:\s+[tT]alk)?:|Special:Contributions/)\s*([^]^[]*?)(?:/[^]^[]*?)?(?:\s*\|[^]^[]*?)?\]\]\s*\S*\s*'

afterUserP = r'\s*(?:(?:\([^)]*?\)\s*)|(?:\[[^]]?\]\s*))*.?'
beforeDateP = r'(?:.?(?:The p|P)receding .*? comment (?:was )?added\s*)?'
#hourdateP = r'(\d\d?:\d\d?,?\s*[0-3]?\d\s+\w+,?\s*20[01]\d(?:\s+\(\w+\))?).?\s*'
hourdateP = r'\s*(\d\d?:\d\d?,?\s*\S*\s*\S*,?\s*20[01]\d(?:\s+\(\w+\))?).?\s*\S*\s*'
#endingP = r'(?:\\&lt.*?)?'
endLine = r'$'
blankP = r'\s*'
manyBlanksP = re.compile(r'\s{5,}')

# signature patterns:
# old: signatureDateP = re.compile(r'(.*)-{0,2}(?:\\&lt;.*?&gt;\s*)?(?:Preceding .*? comment added by )?\[\[(?:User(?:\s+[tT]alk)?:|Special:Contributions/|)\s*([^]^[]*?)(?:/.*?)?(?:\s*[|].*?)?\]\]\s*(?:\(.*?\)\s*)*(?:\\&lt;.*?&gt;)?(?:.?Preceding .*? comment added )?(\d\d?:\d\d?,?\s+[0-3]?\d\s+\w+\s+20[01]\d\s+\(\w+\))\s*(?:\\&lt.*?)?')
signatureDateP = re.compile(textP + htmlP + beforeUserP + userP + htmlP + afterUserP + htmlP + beforeDateP + hourdateP + htmlP + endLine)
# old: dateSignatureP = re.compile(r'(.*)\s*(\d\d?:\d\d?.*)(?:\s*\(UTC\))?\s*(?:\\&lt;.*?&gt;\s*)?(?:Preceding .*? comment added by )?\[\[(?:User:|Special:Contributions/)\s*([^]^[]*?)(?:/.*?)?(?:\s*[|].*?)?\]\](?:\s*\(.*?\))*\s*(?:\\&lt.*?)?')
dateSignatureP = re.compile(textP + htmlP + beforeDateP + hourdateP + htmlP + beforeUserP + userP + htmlP + afterUserP + htmlP + endLine)
# old: signatureP = re.compile(r'(.*)-{0,2}(?:\\&lt;.*?&gt;\s*)?(?:Preceding .*? comment added by )?\[\[(?:User:|Special:Contributions/)\s*([^]^[]*?)(?:/.*?)?(?:\s*[|].*?)?\]\]\s*(?:\(.*?\)\s*)*(?:\\&lt.*?)?')
signatureP = re.compile(textP + htmlP + beforeUserP + userP + afterUserP + htmlP + endLine)
# old: dateP = re.compile(r'(.*)(?:\\&lt;.*?&gt;)?(?:.?Preceding .*? comment added )?(\d\d?:\d\d?.*?)\s*(?:\\&lt.*?)?')
dateP = re.compile(textP + htmlP + beforeDateP + hourdateP + htmlP + endLine)

autoSignatureDateP = re.compile(r'(.*?)\s*\{\{unsigned.*?\|([^}]*?)\|' + hourdateP + r'\}\}\s*$')
autoDateSignatureP = re.compile(r'(.*?)\s*\{\{unsigned.*?\|' + hourdateP + r'\|([^}]*?)\}\}\s*$')
autoSignatureSomethingP = re.compile(r'(.*?)\s*\{\{unsigned.*?\|([^}]*?)\|([^}]*?)\}\}\s*$')
autoSignatureP = re.compile(r'(.*?)\s*\{\{unsigned.*?\|([^}|]*?)\}\}\s*$')

#oldSignature = re.compile(r'(.*)--(\S*?)\s*')
badSignatureP = re.compile(r'(.*)(?<!&lt;!)--(?!&gt;)\s*[\S*]*?\s*' + afterUserP + htmlP + endLine)
oldSeparatorP = re.compile(r'-{4,}\s*$')

startTableP = re.compile(htmlP + r'\s*(?:&lt;table.*?&gt;)' + htmlP)
endTableP = re.compile(htmlP + r'\s*(?:&lt;/table&gt;)' + htmlP)

archiveIndexP = re.compile(r'.*[Aa]rchive.[Ii]ndex$')
