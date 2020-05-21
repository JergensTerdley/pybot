## r6 created by mech ##
##  A simple progam to pull stats using r6tab ##

import sys
import json
from range_key_dict import RangeKeyDict
from event import Event

try:
  import requests
except (ImportError, SystemError):
  print("Warning: r6 module requires requests")
  requests = object
if sys.version_info > (3, 0, 0):
  try:
    from .basemodule import BaseModule
  except (ImportError, SystemError):
    from modules.basemodule import BaseModule
else:
  try:
    from basemodule import BaseModule
  except (ImportError, SystemError):
    from modules.basemodule import BaseModule

"""
For r6 module to work you need to create a file called 'r6_cred.py'
Format it like this:

class R6_Cred:
    api_key = "PuT ApI KeY Here"
 
"""
try: 
    from modules.r6_cred import RsixCred as rc
except (ImportError, SystemError):
    print("Warning: r6 module requires API key in modules/r6_cred.py")

class R6(BaseModule):
  """ Takes specified stats from r6tab and prints them to irc channel """
  def post_init(self):
    r6 = Event("__.r6__")
    r6.define(msg_definition=r"^\.r6")
    r6.subscribe(self)
    self.help = ".r6 <kd,level,rank> <gamer-tag>"
    # register ourself to our new r6 event
    self.bot.register_event(r6, self)
    self.player_ids = []
    self.url = "https://r6.apitab.com/search/uplay/" # URL which outputs JSON data
    self.ranks = RangeKeyDict({
      (0,1199): "Copper V",
      (1200,1299): "Copper IV",
      (1300,1399): "Copper III",
      (1400,1499): "Copper II",
      (1500,1599): "Copper I",
      (1600,1699): "Bronze V",
      (1700,1799): "Bronze IV",
      (1800,1899): "Bronze III",
      (1900,1999): "Bronze II",
      (2000,2099): "Bronze I",
      (2100,2199): "Silver V",
      (2200,2299): "Silver IV",
      (2300,2399): "Silver III",
      (2400,2499): "Silver II",
      (2500,2599): "Silver I",
      (2600,2799): "Gold III",
      (2800,2999): "Gold II",
      (3000,3199): "Gold I",
      (3200,3599): "Platinum III",
      (3600,3999): "Platinum II",
      (4000,4399): "Platinum I",
      (4400,4999): "Diamond",
      (5000,9999): "Champions"
    })

    """
    Example to show json data parameters that can be pulled from with current URL get request:

    level	107
    ranked	
    kd	0.7
    mmr	1881
    rank	6
    champ	0
    NA_mmr	1881
    NA_rank	0
    NA_champ	0
    EU_mmr	0
    EU_rank	0
    EU_champ	0
    AS_mmr	0
    AS_rank	0
    AS_champ	0
    """
  def handle(self, event):
    if len(event.msg.split()) == 3: # Looks for the command and hopefully a valid website (*.com,*.net, etc.)
      try:
        """Needed to set user agent so request would not be blocked, without this a 503 status code is returned"""
        headers = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
                }
        r = requests.get(self.url + event.msg.split()[2] + "?cid=" + rc.api_key, headers=headers)# Takes our static URL and appends your site to the end to make our get request
        j = json.loads(r.text) # Converts our JSON to python object
        for value in j['players']:
          p_id = value
          self.player_ids.append(p_id)
        if j['foundmatch'] == True:
           level = str(j['players'][self.player_ids[0]]['stats']['level']) # Different parameters to choose from
           kd = str(j['players'][self.player_ids[0]]['ranked']['kd'])
           rank = str(j['players'][self.player_ids[0]]['ranked']['mmr'])
           if event.msg.split()[1] == "rank":
             print(self.ranks[int(rank)])
             self.say(event.channel, rank + " | " + self.ranks[int(rank)])
             self.player_ids.clear()
           elif event.msg.split()[1] == "kd":
             self.say(event.channel, kd)
             self.player_ids.clear()
           elif event.msg.split()[1] == "level":
             self.say(event.channel, level)
             self.player_ids.clear()
        else:
          if len(j['players']) == 0:
            self.say(event.channel, "No player found.")
          else:
            for i in self.player_ids:
              check_case = event.msg.split()[2] is j['players'][i]['profile']['p_name']
              if check_case == True:
                print(event.msg.split()[2]+ " " + j['players'][i]['profile']['p_name'] + " " + "FOUND MATCH")
              else:
                continue
            self.player_ids.clear()
            self.say(event.channel, "Multiple matches found, check spelling and case.")

      except requests.ConnectionError:
        self.say(event.channel, "Connection error.")
      except KeyError:
        self.say(event.channel, "No API key found")
