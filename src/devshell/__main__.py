from .shell import DevshellCmd
from argparse import ArgumentParser

argparser = ArgumentParser(description='''devshell is a tool to help make doctests.

Run without arguments to enter the devshell shell at the current working directory.

Run with the --target argument specifying the fully qualified name of a docstring-supportable item to enter the devshell shell, navigate to that object, and enter an interactive recording session for that object.''')
argparser.add_argument('-d','--directory',help='Path to make the current working directory')
argparser.add_argument('-t','--target',help='fully qualified name of a package, module, class, or function')
args = argparser.parse_args()
shell = DevshellCmd()
print('\nStarting devshell command line interface...')
if args.directory:
    shell.onecmd('chdir %s' % args.directory)
if args.target:
    shell.onecmd('cd %s' % args.target)
shell.cmdloop()
