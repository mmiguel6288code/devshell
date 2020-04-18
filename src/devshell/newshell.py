import sys, string, shlex, textwrap
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit import PromptSession

class Devshell():
    prompt = [('class:prompt','(devshell)$ ')]
    identifer_chars = string.ascii_letters + string.digits + '_'
    style = Style.from_dict({
        'prompt':'#6600ff',
        })
    nohelp = "*** No help on %s"
    def __init__(self,stdin=None,stdout=None,intro=None,interactive=True):
        if stdin is None:
            stdin = sys.stdin
        if stdout is None:
            stdout = sys.stdout
        self.stdin = stdin
        self.stdout = stdou
        self.psession = PromptSession(**psession_kwargs)
        self.intro = intro
        self.cmdqueue = []
        self.interactive = interactive

    def cmdloop(self,intro=None):
        self.preloop()

        if self.intro is not None:
            self.stdout.write(str(self.intro)+"\n")
        stop = None
        while not stop:
            if len(self.cmdqueue) > 0:
                line = self.cmdqueue.pop(0)
            else:
                if self.interactive:
                    try:
                        line = self.psession.prompt(self.prompt)
                    except EOFError:
                        line = 'EOF'
                else:
                    self.stdout.write(self.prompt)
                    self.stdout.flush()
                    line = self.stdin.readline()
                    if not len(line):
                        line = 'EOF'
                    else:
                        line = line.rstrip('\r\n')
            line = self.precmd(line)
            stop = self.onecmd(line)
            stop = self.postcmd(stop, line)
        self.postloop()

    def preloop(self):
        pass
    def precmd(self,line):
        return line
    def onecmd(self, line):
        full_cmd = shlex.split(line)
        if len(full_cmd) == 0:
            return
        cmd = full_cmd[0]
        if line == 'EOF' :
            self.lastcmd = ''
        else:
            self.lastcmd = line
        if hasattr(self,'do_'+cmd):
            return getattr(self,'do_'+cmd)(*full_cmd[1:])
        else:
            return self.default(line)
    def default(self,line):
        ...

    def postcmd(self, stop, line):
        """Hook method executed just after a command dispatch is finished."""
        return stop
    def postloop(self):
        pass

    def do_help(self, *args):
        'List available commands with "help" or detailed help with "help cmd".'
        if len(args) == 1:
            arg = args[0]
            if hasattr(self,'help_'+arg):
                getattr(self,'help_'+arg)()
                return
            elif hasattr(self,'do_'+arg):
                doc = getattr(self,'do_'+arg).__doc__
                if doc:
                    self.stdout.write(str(doc)+'\n')
                    return
           self.stdout.write((self.nohelp % arg) + '\n')
        elif len(args) == 0:
            names = dir(self.__class__)
            cmds_doc = []
            cmds_undoc = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]]=1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd=name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
            self.stdout.write("%s\n"%str(self.doc_leader))
            self.print_topics(self.doc_header,   cmds_doc,   15,80)
            self.print_topics(self.misc_header,  list(help.keys()),15,80)
            self.print_topics(self.undoc_header, cmds_undoc, 15,80)
        else:
            print('help command not understood')

    def print_topics(self, header, cmds, cmdlen, maxcol):
        if cmds:
            self.stdout.write("%s\n"%str(header))
            if self.ruler:
                self.stdout.write("%s\n"%str(self.ruler * len(header)))
            self.columnize(cmds, maxcol-1)
            self.stdout.write("\n")


class DevshellCompleter(Completer):
    def __init__(self,devshell):
        self.devshell = devshell
    def get_completions(self,document,complete_event):
            yield Completion(suggestion,start_position=0)
