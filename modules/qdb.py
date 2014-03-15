from event import Event
import requests

class QDB:
    def __init__(self, events=None, printer_handle=None, bot=None):
        self.events = events
        self.printer = printer_handle
        self.interests = ['__.qdb__'] 
        self.bot = bot
        self.bot.mem_store['qdb'] = {} 

	qdb = Event("__.qdb__")
	qdb.define(msg_definition=".*")
        qdb.subscribe(self)

        #qdb_buff = Event("__qdb_buff__")
        #qdb_buff.define(msg_definition=".*")
        #qdb_buff.subscribe(self)

	self.bot.register_event(qdb, self)
        #self.bot.register_event(qdb_buff, self)

        self.help = ".qdb <search string of first line> | <search string of last line>"
        self.MAX_BUFFER_SIZE = 100 

    def add_buffer(self, event=None): 
        """Takes a channel name and line passed to it and stores them in the bot's mem_store dict
        for future access. The dict will have channel as key. The value to that key will be a list
        of dicts associating a username with the message they posted.
        If the buffer size is not yet exceeded, lines are just added. If the buffer
        is maxed out, the oldest line is removed and newest one inserted at the beginning.
        """
        if not event:
            return
        #create a dictionary associating the channel with an empty list if it doesn't exist yet
        if event.channel not in self.bot.mem_store['qdb']:
            self.bot.mem_store['qdb'][event.channel] = []
        try:
        #check for the length of the buffer. if it's too long, pop the last item
            if len(self.bot.mem_store['qdb'][event.channel]) >= self.MAX_BUFFER_SIZE:
                self.bot.mem_store['qdb'][event.channel].pop()
            #define a line as a dict associating user to msg
            #insert the line into the first position in the list
            line = {event.user:event.msg}
            self.bot.mem_store['qdb'][event.channel].insert(0, line)
        except KeyError:
            print "QDB add_buffer() error. Couldn't find dictionary key."
        except IndexError:
            print "QDB add_buffer() error. Couldn't access the list index."

    def format_line(self, line):
        """Takes a dict with a nick:msg relationship and formats it for QDB submission"""
        if len(line) != 1:
            return "\n"
        try:
            nick = line.keys()[0].strip()
            msg = line.values()[0]
            #special formatting for ACTION strings
            if msg.startswith('\001ACTION'): 
                #strip out the word ACTION from the msg
                msg = msg[7:]
                return ' * %s %s\n' % (nick, msg)
            else:
                return '<%s > %s\n' % (nick, msg)
        except KeyError:
            print "QDB format_line() error. Couldn't find dictionary keys."
        except IndexError:
            print "QDB format_line() error. Couldn't get selected index from list."

    def get_qdb_submission(self, channel=None, start_msg='', end_msg=''):
        """Given two strings, start_msg and end_msg, this function will assemble a submission for the QDB.
        start_msg is a substring to search for and identify a starting line. end_msg similarly is used
        to search for the last desired line in the submission. This function returns a string ready
        for submission to the QDB if it finds the desired selection. If not, it returns None.
        """
        #must have at least one msg to search for and channel to look it up in
        if len(start_msg) == 0 or not channel:
            return None
        #first, check to see if we are doing a single string submission.
        if end_msg == '':
            for line in self.bot.mem_store['qdb'][channel]:
                #self.bot.mem_store['qdb'][channel][i] will contain a dict with only one key:value pair
                if start_msg in line.values()[0]:
                    return self.format_line(line)
            #making sure we get out of the function if no matching strings were found
            #don't want to search for a nonexistent second string later
            return None
        #search for a matching start and end string and get the buffer index for the start and end message
        start_index = -1
        end_index = -1
        #goes through all lines in buffer
        #not really a bug, but if the same string is found multiple times, it will choose the oldest one
        for index, line in enumerate(self.bot.mem_store['qdb'][channel]):
            if start_msg in line.values()[0]:
                start_index = index
            if end_msg in line.values()[0]:
                end_index = index
        #check to see if index values are positive. if not, string was not found and we're done
        if start_index == -1 or end_index == -1 or start_index < end_index:
            return None
        #now we generate the string to be returned for submission
        submission = ''
        try:
            for i in reversed(range(end_index, start_index + 1)):
                #print 'Index number is ' + str(i) + ' and current submission is ' + submission
                submission += self.format_line(self.bot.mem_store['qdb'][channel][i])
        except IndexError:
            print "QDB get_qdb_submission() error when accessing list index"
        except KeyError:
            print "QDB get_qdb_submission() error when retrieving dict keys"
        return submission

    def submit(self, qdb_submission):
        """Given a string, qdb_submission, this function will upload the string to hlmtre's qdb
        server. Returns a string with status of submission. If it worked, includes a link to new quote. 
        """ 
        #accessing hlmtre's qdb api
        url = 'http://qdb.zero9f9.com/api.php'
        payload = {'q':'new', 'quote': qdb_submission.rstrip('\n')}
        qdb = requests.post(url, payload)
        #check for any HTTP errors and return False if there were any
        try:
            qdb.raise_for_status()
        except requests.exceptions.HTTPError:
            return "HTTPError encountered when submitting to QDB"
        try:
            q_url = qdb.json()
            return "QDB submission successful! http://qdb.zero9f9.com/quote.php?id=" + str(q_url['id'])
        except (KeyError, UnicodeDecodeError):
            return "Error getting status of quote submission." 
        return "That was probably successful since no errors came up, but no status available."

    def handle(self, event):
        #first we see if we're going to generate a qdb submission, or just add the line to the buffer
        if event.msg.startswith(".qdb "):
            #split the msg with '.qdb ' stripped off beginning and divide into 1 or 2 search strings
            string_token = event.msg[5:].split('|', 1)
            start_msg = string_token[0].rstrip()
            #see if we only have a one line submission
            if len(string_token) == 1:
                #s is the string to submit
                s = self.get_qdb_submission(event.channel, start_msg)
                if not s:
                    self.printer("PRIVMSG " + event.channel + ' :QDB Error: Could not find requested string.\n')
                    return
                #Print the link to the newly submitted quote
                self.printer("PRIVMSG " + event.channel + ' :' + self.submit(s) + '\n')
                return
            #We should only get here if there are two items in string_token
            end_msg = string_token[1].lstrip()
            s = self.get_qdb_submission(event.channel, start_msg, end_msg)
            #if there's nothing found for the submission, then we alert the channel and gtfo
            if not s: 
                self.printer("PRIVMSG " + event.channel + ' :QDB Error: Could not find requested quotes.\n')
                return
            #print the link to the new submission
            self.printer("PRIVMSG " + event.channel + ' :' + self.submit(s) + '\n')
            return
        #we only want lines that are PRIVMSGs
        if "PRIVMSG" in event.line:
            self.add_buffer(event)
        #self.printer("PRIVMSG " + event.channel + ' :QDB' + '\n')