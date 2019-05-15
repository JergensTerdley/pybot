##Hold me closer tiny dancer##

import sys
from event import Event

try:
  if sys.version_info > (3, 0, 0):
    from .basemodule import BaseModule
  else:
    from basemodule import BaseModule
except (ImportError, SystemError):
  from modules.basemodule import BaseModule

class Dance(BaseModule):

  def post_init(self):
    dance = Event("__.dance__")
    dance.define(msg_definition="^.dance$")
    dance.subscribe(self)
    self.cmd = ".dance"
    self.help = ".dance (bot dances)"

    self.bot.register_event(dance, self)

  def handle(self, event):
    try:
      self.printer("PRIVMSG " + event.channel + " : :D-\-< " + '\n') #Prints this dancing guy out to proper channel
      self.printer("PRIVMSG " + event.channel + " : :D-|-< " + '\n')
      self.printer("PRIVMSG " + event.channel + " : :D-/-< " + '\n')
    except TypeError:
      pass
