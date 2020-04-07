import re, ast, logging, argparse, os
from xml.dom import minidom
from . import messages
from .pyonvif import NoCameraFoundException, OnvifCam


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
   parser.add_argument("-a", "--address", help="camera address (and optionally :port)")
   parser.add_argument("-s", "--servicepath", help="service path", default="/onvif/device_service")
   parser.add_argument("-p", "--profile", help="profile")
   parser.add_argument("-u", "--user", help="username", default=None)
   parser.add_argument("-v", "--verbose", action='store_true', help="Log level")

   subparsers = parser.add_subparsers(title='onvif commands',
                                      description='valid commands are listed below',
                                      help='enter command name and parameters',
                                      dest="_cmd")

   cmds = get_commands()
   for cmd, parms in cmds.items():
      hlp = cmd.lower().replace('_', ' ').capitalize()
      cmdparser = subparsers.add_parser(cmd, help=hlp)
      for parm in parms:
         cmdparser.add_argument(parm, type=str, help=parm + " argument")

   args = parser.parse_args()

   if not args._cmd:
      parser.print_help()
      parser.exit()

   if args.verbose:
      logging.basicConfig(level=logging.DEBUG)

   pwd = None
   if args.user:
      pwd = os.environ.get("CAMERA_PASSWORD")
      if not pwd:
         parser.exit(message="no password; please add it as CAMERA_PASSWORD to shell environment\n")

   try:
      addr, port = args.address.split(':')
   except:
      addr = args.address
      port = 80

   try:
      c = OnvifCam(addr=addr, port=port, pth=args.servicepath, prf=args.profile, usr=args.user, pwd=pwd,\
                   verbose=args.verbose)
   except NoCameraFoundException:
      parser.exit(message="no camera found\n")

   result = c.execute(args._cmd, **dict(args._get_kwargs()))
   if result:
      tree = minidom.parseString(result)
      body = tree.getElementsByTagName("SOAP-ENV:Body")[0]
      for n in body.childNodes:
         print(n.toprettyxml())
      return

