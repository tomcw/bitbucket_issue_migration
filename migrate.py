# This file is part of the bitbucket issue migration script.
#
# The script is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# The script is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with the bitbucket issue migration script.
# If not, see <http://www.gnu.org/licenses/>.

#https://docs.python.org/2/library/stdtypes.html

from pygithub3 import Github
from datetime import datetime, timedelta
from HTMLParser import HTMLParser
from htmlentitydefs import name2codepoint

import urllib2
import time
import getpass

import sys

try:
    import json
except ImportError:
    import simplejson as json

import xml.etree.ElementTree as ET
bug_tree = ET.parse('F:\\Apple][\\AppleWin\\berlios\\bug_dump.php')
bug_root = bug_tree.getroot()
feature_tree = ET.parse('F:\\Apple][\\AppleWin\\berlios\\feature_dump.php')
feature_root = feature_tree.getroot()

from optparse import OptionParser
parser = OptionParser()

#######################################
#bug_category_id	category_name
bug_category_id_to_name={
100:    'none',   
1505:	'1.12.8.0',
1506:	'1.12.9.0',
1507:	'1.12.9.1',
1508:	'Pre-1.12.8',
1525:	'1.13.0',
1528:	'1.13.1',
2297:	'1.19.3',
1900:	'1.13.2',
1995:	'1.14.0',
1996:	'1.14.1',
2099:	'1.15.0 (beta)',
2100:	'1.14.2',
2138:	'1.16.0 (beta)',
2196:	'1.16.1',
2247:	'1.17.1',
2248:	'1.17.2',
2256:	'1.18.0 (beta)',
2259:	'1.18.1 (beta)',
2275:	'1.19.0',
2305:	'1.20.0',
2374:	'1.20.1',
2375:	'1.21.1',
2385:	'1.22.0',
2390:	'1.23.0',
2402:	'1.24.0'}

#bug_group_id	group_name
bug_group_id_to_name={
100:    'none',
635:	'Unreproducible',
636:	'Future request'}

#status_id (bug)
bug_status_id_to_name={
1: 'Open',
2: 'Unknown',
3: 'Closed'}

#feature_category_id	category_name
feature_category_id_to_name={
100:    'none',   
10784:	'Debug',
10785:	'User Interface',
10786:	'General Functionality',
10891:	'New Hardware'}

#status_id (feature)
feature_status_id_to_name={
1: 'Open',
2: 'Closed',
3: 'Deleted'}

#kUTC_Offset = 60*60     # +1 hour - for Germany? But not all Bugs need this offset, eg. Bug #18940
kUTC_Offset = 0
kUTC_Feature_Offset = 60*60

#######################################

# F:\dev\berlios_issues\bitbucket_issue_migration>migrate.py -g tomcw -d tomcw/test

"""
parser.add_option("-t", "--dry-run", action="store_true", dest="dry_run", default=False,
    help="Preform a dry run and print eveything.")

parser.add_option("-g", "--github-username", dest="github_username",
    help="GitHub username")

parser.add_option("-d", "--github_repo", dest="github_repo",
    help="GitHub to add issues to. Format: <username>/<repo name>")

(options, args) = parser.parse_args()

print 'Please enter your github password'
github_password = getpass.getpass()
"""

#DEBUG
(options, args) = parser.parse_args()
options.github_username = "tomcw"
options.github_repo = "tomcw/test4"
#options.dry_run = True     # Unsupported
github_password = ?
#DEBUG(END)

# Login in to github and create object
github = Github(login=options.github_username, password=github_password)

userId_to_name = {
0: 'Unknown',
26317: 'blurry',
41180: 'ohdog',
62046: 'pacmanbg',
64112: 'benoit0123'
}

github_issues = []  # empty list

####

def get_features():
    for feature in feature_root:
        id_str = feature.attrib['id']
        url_str = "http://developer.berlios.de/feature/?func=detailfeature&feature_id=" + id_str + "&group_id=6117"
        content = urllib2.urlopen(url_str).read()
        f = open('F:\\Apple][\\AppleWin\\berlios\\features\\' + id_str + '.html', 'wb')
        f.write(content)
        f.close()
        
####

# https://docs.python.org/2/library/htmlparser.html

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    ph = 0
    h2 = False
    pre = False
    history_list = []
    s = ''
    def MyInit(self, id):
        self.id = id
    def handle_starttag(self, tag, attrs):
        if self.ph == 0 and tag == 'h2':
            self.h2 = True
        if self.ph == 1 and tag == 'pre':
            self.pre = True
    def handle_endtag(self, tag):
        if self.ph == 0 and tag == 'h2':
            self.h2 = False
        if self.ph == 1 and tag == 'pre':
            self.pre = False
            self.history_list.insert(0, self.s) # Insert at front of list (as items come in newest to oldest order, but we want oldest first)
            self.s = ''
        if self.ph == 1 and self.pre == False and tag == 'table':
            self.ph = 2
    def handle_data(self, data):
        if self.ph == 0 and self.h2 and data.find(str(self.id)) >= 0:
            self.ph = 1
        if self.ph == 1 and self.pre:
            data = data.replace('\x92', '\x27')
            data = data.replace('\x93', '\x22')
            data = data.replace('\x94', '\x22')
            self.s = self.s + data
    def handle_entityref(self, name):
        if self.ph == 1 and self.pre:
            c = unichr(name2codepoint[name])
            self.s = self.s + c

def parse_feature(id):
    parser = MyHTMLParser()
    parser.MyInit(id)
    parser.feed(open('F:\\Apple][\\AppleWin\\berlios\\features\\' + str(id) + '.html').read())
    parser.close()
    return parser.history_list


####

def create_berliosId_mapping():
    for bug in bug_root:
        submitted_by_id   = int( bug.find('submitted_by').attrib['id'] )
        submitted_by_name = bug.find('submitted_by').attrib['name']
        userId_to_name[submitted_by_id] = submitted_by_name

        assigned_to_id   = int( bug.find('assigned_to').attrib['id'] )
        assigned_to_name = bug.find('assigned_to').attrib['name']
        userId_to_name[assigned_to_id] = assigned_to_name

    for feature in feature_root:
        submitted_by_id   = int( feature.find('submitted_by').attrib['id'] )
        submitted_by_name = feature.find('submitted_by').attrib['name']
        userId_to_name[submitted_by_id] = submitted_by_name

        assigned_to_id   = int( feature.find('assigned_to').attrib['id'] )
        assigned_to_name = feature.find('assigned_to').attrib['name']
        userId_to_name[assigned_to_id] = assigned_to_name

####

def add_new_labels():
	res_labels = github.issues.labels.list(options.github_repo.split('/')[0], options.github_repo.split('/')[1] )
	num_labels = 0
	for page in res_labels:
		for resource in page:
			num_labels+=1
	if num_labels > 7:    # GitHub repo defaults to 7
		print "(Labels already added. Total={})".format(num_labels)
		return

	# Add new labels
	for bug_category in bug_category_id_to_name:
		label_data = {'name': bug_category_id_to_name[bug_category].encode('utf-8'),
					  'color': "FFFFFF".encode('utf-8')}
		res_new = github.issues.labels.create(label_data, options.github_repo.split('/')[0], options.github_repo.split('/')[1] )
		
	print "add_new_labels(): Done!"

####

# Create issues in the order that BUGS were created in Berlios:
# - this isn't the order that they appear in the input XML file.
# - need to merge in the Berlios FEATURES too

def create_bug_hdr(ts, bug_id_str, submitted_by, category_id, bug_group_id, assigned_to, priority):
    return '**BerliOS Bug #' + bug_id_str + '**\n\n' +\
           '**Date:** ' + datetime.fromtimestamp(ts+kUTC_Offset).strftime('%Y-%B-%d %H:%M') + '\n'\
           '**Submitted By:** ' + submitted_by + '\n'\
           '**Category:** ' + bug_category_id_to_name[category_id] + '\n'\
           '**Bug Group:** ' + bug_group_id_to_name[bug_group_id] + '\n'\
           '**Assigned To:** ' + assigned_to + '\n'\
           '**Priority:** ' + str(priority) + '\n\n====\n\n'\

####

def create_feature_hdr(ts, feature_id_str, submitted_by, category_id, assigned_to, priority):
    return '**BerliOS Feature Request #' + feature_id_str + '**\n\n' +\
           '**Date:** ' + datetime.fromtimestamp(ts+kUTC_Offset).strftime('%Y-%B-%d %H:%M') + '\n'\
           '**Submitted By:** ' + submitted_by + '\n'\
           '**Category:** ' + feature_category_id_to_name[category_id] + '\n'\
           '**Assigned To:** ' + assigned_to + '\n'\
           '**Priority:** ' + str(priority) + '\n\n====\n\n'\

####

def timestamp_hdr(ts, utc_offset, user):
    return '[' + datetime.fromtimestamp(ts+utc_offset).strftime('%Y-%B-%d %H:%M') + ', by: ' + user + ']\n\n'

####

def add_bugs_to_list():
    bug_count = 0
    for bug in bug_root:
        bug_id_str   = bug.attrib['id']
        status_id    = int( bug.find('status_id').text )
        priority     = int( bug.find('priority').text )
        category_id  = int( bug.find('category_id').text )
        submitted_by_name = bug.find('submitted_by').attrib['name']
        assigned_to_name  = bug.find('assigned_to').attrib['name']
        timestamp_opened  = int( bug.find('date').text )
        summary = bug.find('summary').text
        details = bug.find('details').text
        #timestamp_closed  = int( bug.find('close_date').text )    # 0 = still open
        bug_group_id      = int( bug.find('bug_group_id').text )
    
        bug_hdr = create_bug_hdr(timestamp_opened, bug_id_str, submitted_by_name, category_id, bug_group_id, assigned_to_name, priority)

        assignee = 'tomcw' if assigned_to_name == 'tomch' else ''
        issue = [timestamp_opened,
                 summary.encode('utf-8'),                                                       # title
                 bug_hdr + details.encode('utf-8'),                                             # body
                 assignee.encode('utf-8'),                                                      # assignee
                 ["bug".encode('utf-8'), bug_category_id_to_name[category_id].encode('utf-8')], # labels
                 status_id,
                 []                                                                             # history
                ]

        for history in bug.iter('history'):
            ts     = int( history.find('date').text )
            userId = int( history.find('mod_by').text )
            user = 'Unknown'
            if userId in userId_to_name:
                user = userId_to_name[userId]
            else:
                print 'Unknown userId:' + str(userId) + ' - Bug# ' + bug_id_str
            if history.find('field_name').text == 'details':
                issue[6].append( timestamp_hdr(ts, kUTC_Offset, user) + history.find('old_value').text )
            elif history.find('field_name').text == 'close_date':
                issue[6].append( timestamp_hdr(ts, kUTC_Offset, user) + 'Closed.' )
            elif history.find('field_name').text == 'category_id':
                pass
            elif history.find('field_name').text == 'assigned_to':
                pass
            elif history.find('field_name').text == 'status_id':
                pass
            elif history.find('field_name').text == 'resolution_id':
                pass
            elif history.find('field_name').text == 'summary':
                pass
            elif history.find('field_name').text == 'priority':
                pass
            elif history.find('field_name').text == 'bug_group_id':
                pass
            else:
                print history.find('field_name').text

        bug_count += 1
        github_issues.append(issue)
        #break   ### DEBUG

    return bug_count

####

# Features with non-ascii chars:
# . #3517 (char=0xA1)
# . #2337 (char=0x93/0x94) Angled double-quotes -> converted to 0x22 in html parser
# . #5557 (char=0x92) Single-quote              -> converted to 0x27 in html parser

def add_features_to_list():
    feature_count = 0
    for feature in feature_root:
        feature_id_str   = feature.attrib['id']
        status_id    = int( feature.find('status_id').text )
        priority     = int( feature.find('priority').text )
        category_id  = int( feature.find('category_id').text )
        submitted_by_name = feature.find('submitted_by').attrib['name']
        assigned_to_name  = feature.find('assigned_to').attrib['name']
        timestamp_opened  = int( feature.find('date').text )
        summary = feature.find('summary').text
        #details = feature.find('details').text                        # Always empty for features
        #timestamp_closed  = int( feature.find('close_date').text )    # 0 = still open
        #feature_group_id  = int( feature.find('bug_group_id').text )  # NB. No equivalent for features

        #if feature_id_str != '5557':    ### DEBUG
        #    continue
    
        #

        history_list = parse_feature( int(feature_id_str) )
        if len(history_list) == 0:
            continue                    # Empty for deleted features

        details = history_list.pop(0)

        ### Calc tz_offset

        #details2 = details.lstrip('\n')
        #str2 = details2[0:4]

        #if details2[0:4] == 'Date':
        #    line0_str = details2.splitlines()[0]
        #    hour1 = int( line0_str[ len(line0_str)-6:len(line0_str)-3 ] )
        #    dateopened_str = datetime.fromtimestamp(timestamp_opened).strftime('%Y-%B-%d %H:%M')
        #    hour2 = int( dateopened_str[ len(dateopened_str)-6:len(dateopened_str)-3 ] )
        #    tz_offset = (hour1 - hour2) * 60 * 60
        #    if tz_offset != 0:
        #        print "-ve"

        #print "tz diff = " + str( tz_offset/3600 )

        #

        timestamp_opened = timestamp_opened + kUTC_Feature_Offset

        feature_hdr = create_feature_hdr(timestamp_opened, feature_id_str, submitted_by_name, category_id, assigned_to_name, priority)

        assignee = 'tomcw' if assigned_to_name == 'tomch' else ''
        issue = [timestamp_opened,
                 summary.encode('utf-8'),                                                       # title
                 feature_hdr + details.encode('utf-8'),                                         # body
                 assignee.encode('utf-8'),                                                      # assignee
                 ["enhancement".encode('utf-8')],                                               # labels
                 status_id,
                 []                                                                             # history
                ]

        issue[6] = list(history_list)   # Copy the list

        while len(history_list):        # Clear the list
            history_list.pop()

        for history in feature.iter('history'):
            ts     = int( history.find('date').text )
            userId = int( history.find('mod_by').text )
            user = 'Unknown'
            if userId in userId_to_name:
                user = userId_to_name[userId]
#            if history.find('field_name').text == 'details':                                   # Not in the exported file - use HTML pages instead
#                issue[6].append( timestamp_hdr(ts, kUTC_Feature_Offset, user) + history.find('old_value').text )
            if history.find('field_name').text == 'close_date':
                issue[6].append( timestamp_hdr(ts, kUTC_Feature_Offset, user) + 'Closed.' )
            elif history.find('field_name').text == 'category_id':
                pass
            elif history.find('field_name').text == 'assigned_to':
                pass
            elif history.find('field_name').text == 'status_id':
                pass
            elif history.find('field_name').text == 'resolution_id':
                pass
            elif history.find('field_name').text == 'summary':
                pass
            elif history.find('field_name').text == 'priority':
                pass
            elif history.find('field_name').text == 'feature_status_id':
                pass
            elif history.find('field_name').text == 'feature_category_id':
                pass
            else:
                print history.find('field_name').text

        feature_count += 1
        github_issues.append(issue)
        #break   ### DEBUG

    return feature_count

####

def add_new_issues():
    issue_count = 0
    for issue in github_issues:

        # Create the issue: https://developer.github.com/v3/issues/
        issue_data = {'title': issue[1],
                      'body': issue[2],
			          'assignee': issue[3],
			          'labels': issue[4],
                      }
        if issue[3] == '':
            del issue_data['assignee']
        ni = github.issues.create(issue_data, options.github_repo.split('/')[0], options.github_repo.split('/')[1] )

        for history in issue[6]:
                create_res = github.issues.comments.create(ni.number,
                                     history,
                                     options.github_repo.split('/')[0],
                                     options.github_repo.split('/')[1])

                errorCount = 0;
                while (errorCount < 10):
                    try:
                        comment_res = github.issues.comments.get(create_res.id,         # Serialise creation of comments
                                             user=options.github_repo.split('/')[0],
                                             repo=options.github_repo.split('/')[1])
                        break
                    except:                                                             # Sometimes get a "NotFound: 404 - Not Found" exception
                        errorCount = errorCount + 1
                        time.sleep(0.200)

                if errorCount >= 10:
                    print "Failed to get comment - aborting at issue #" + str(issue_count)
                    return

        if issue[5] != 1:
                github.issues.update(ni.number,
                                     {'state': 'closed'},
                                     user=options.github_repo.split('/')[0],
                                     repo=options.github_repo.split('/')[1])

        issue_count = issue_count + 1

####

#def process_bugs():
#    bug_count = 0
#    for bug in bug_root:
#        bug_id_str   = bug.attrib['id']
#        status_id    = int( bug.find('status_id').text )          # Unused. For bugs either Open or Closed.
#        priority     = int( bug.find('priority').text )
#        category_id  = int( bug.find('category_id').text )
#        submitted_by_name = bug.find('submitted_by').attrib['name']
#        assigned_to_name  = bug.find('assigned_to').attrib['name']
#        timestamp_opened  = int( bug.find('date').text )
#        summary = bug.find('summary').text
#        details = bug.find('details').text
#        timestamp_closed  = int( bug.find('close_date').text )    # 0 = still open
#        bug_group_id      = int( bug.find('bug_group_id').text )
    
#        bug_hdr = create_bug_hdr(timestamp_opened, bug_id_str, submitted_by_name, category_id, bug_group_id, assigned_to_name, priority)

#        # Create the issue: https://developer.github.com/v3/issues/
#        assignee = 'tomcw' if assigned_to_name == 'tomch' else ''
#        issue_data = {'title': summary.encode('utf-8'),
#                      'body': bug_hdr + details.encode('utf-8'),
#			          'assignee': assignee.encode('utf-8'),
#			          'labels': ["bug".encode('utf-8'), bug_category_id_to_name[category_id].encode('utf-8')]
#                      }
#        if assignee == '':
#            del issue_data['assignee']
#        ni = github.issues.create(issue_data, options.github_repo.split('/')[0], options.github_repo.split('/')[1] )

#        # NB.add_to_issue() broken: https://github.com/copitux/python-github3/issues/34
#        # github.issues.labels.add_to_issue(ni, options.github_repo.split('/')[0], options.github_repo.split('/')[1], bug_category_id_to_name[category_id].encode('utf-8') )

#        for history in bug.iter('history'):
#            ts     = int( history.find('date').text )
#            userId = int( history.find('mod_by').text )
#            user = 'Unknown'
#            if userId in userId_to_name:
#                user = userId_to_name[userId]
#            if history.find('field_name').text == 'details':
#                # NB. Sometime Github comments are out of chronological order wrt Berlios history items, eg. BerliOS Bug #19109
#                github.issues.comments.create(ni.number,
#                                              timestamp_hdr(ts, user) + history.find('old_value').text,
#                                              options.github_repo.split('/')[0],
#                                              options.github_repo.split('/')[1])
#            elif history.find('field_name').text == 'category_id':
#                pass
#            elif history.find('field_name').text == 'assigned_to':
#                pass
#            elif history.find('field_name').text == 'status_id':
#                pass
#            elif history.find('field_name').text == 'resolution_id':
#                pass
#            elif history.find('field_name').text == 'summary':
#                pass
#            elif history.find('field_name').text == 'close_date':
#                github.issues.comments.create(ni.number,
#                                              timestamp_hdr(ts, user) + 'Closed.',
#                                              options.github_repo.split('/')[0],
#                                              options.github_repo.split('/')[1])
#                github.issues.update(ni.number,
#                                     {'state': 'closed'},
#                                     user=options.github_repo.split('/')[0],
#                                     repo=options.github_repo.split('/')[1])
#            else:
#                pass

#        bug_count += 1
#        print '.'

#    print '\n'
#    return bug_count

###

#get_features() # Read all the Feature HTML pages from Berlios
#history_list = parse_feature(2053) # test

create_berliosId_mapping()

bug_count     = add_bugs_to_list()
feature_count = add_features_to_list()

github_issues.sort(key = lambda issue: issue[0])

add_new_labels()    # for bug categories
add_new_issues()

print "Created {} BUGs and {} FEATUREs = {} total issues".format(bug_count, feature_count, bug_count+feature_count)

sys.exit()
