import re, ast, logging, argparse
from pyonvif import messages, OnvifCam


log = logging.getLogger(__name__)


def get_commands():
    "return list of available commands & their params"

    xpr = re.compile("{[a-z_]+}")
    cmds = {}
    with open(messages.__file__) as msgsf:
       msgs = ast.parse(msgsf.read())
       for i in msgs.body:
          if isinstance(i, ast.Assign):
             cmd = i.targets[0].id
             if cmd.startswith('_'):
                 continue
             parms = [p.strip('{}') for p in re.findall(xpr, i.value.s)] or []
             cmds[cmd] = parms
    return cmds


def command():
   "the command-line client"

   parser = argparse.ArgumentParser()
   parser.add_argument("command", metavar="CMD", default='', nargs='*', type=str, help="Onvif command to send")
   parser.add_argument("-a", "--address", help="camera address")
   parser.add_argument("-p", "--path", help="command path", default="/onvif/device_service")
   #parser.add_argument("-a", "--auth", help="user credentials (-a username,passwd)")
   parser.add_argument("-c", "--commands", action='store_true', help="get available commands")
   parser.add_argument("-l", "--loglevel", action='store_true', help="Log level")

   args = parser.parse_args()

   if args.loglevel:
      logging.basicConfig(level=logging.DEBUG)

   if args.commands:
      cmds = get_commands()
      print("Available commands & their arguments:\n")
      for c, parms in cmds.items():
         print("   " + c + ' ' + ', '.join(parms))
