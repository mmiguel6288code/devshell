"""
This script takes the Cmd object from the built-in standard library, adds an input_method attribute, and replaces all calls to the standard input() with calls to the input_method attribute
"""
import ast, inspect, cmd, shlex
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit import PromptSession


class PTCmd_Completer(Completer):
    def __init__(self,ptcmd):
        self.ptcmd = ptcmd
    def get_completions(self,document,complete_event):
        for suggestion in self.ptcmd.pt_complete(document,complete_event):
            #yield Completion(suggestion,start_position=0)
            try:
                yield Completion(suggestion,-len(shlex.split(document.current_line_before_cursor)[-1]))
            except:
                pass
class PTCmd(cmd.Cmd):
    def __init__(self, completekey='tab', stdin=None, stdout=None,**psession_kwargs):
        super().__init__(completekey,stdin,stdout)
        psession_kwargs['completer'] = PTCmd_Completer(self)
        psession_kwargs['complete_while_typing'] = True
        self.psession = PromptSession(**psession_kwargs)
        self.input_method = self.psession.prompt
    def pt_complete(self, document,complete_event):
        origline = document.text
        line = origline.lstrip()
        stripped = len(origline) - len(line)
        begidx = document.cursor_position_col - stripped
        endidx = len(document.text) - stripped
        if begidx>0:
            cmd, args, foo = self.parseline(line)
            if cmd == '':
                compfunc = self.completedefault
            else:
                try:
                    compfunc = getattr(self, 'complete_' + cmd)
                except AttributeError:
                    compfunc = self.completedefault
        else:
            compfunc = self.completenames
        self.completion_matches = compfunc(document.text, line, begidx, endidx)
        yield from self.completion_matches


class SwitchInput(ast.NodeTransformer):
    def visit_Call(self,node):
        if isinstance(node.func,ast.Name) and node.func.id == 'input':
            load = ast.Load()
            return ast.Call(
                    func = ast.Attribute(
                            value=ast.Name(
                                id='self',
                                ctx=load,
                                ),
                            attr='input_method',
                            ctx=load,
                        ),
                    args=node.args,
                    keywords=node.keywords,
                    )
        else:
            return node

ptcmd_tree = ast.parse(inspect.getsource(PTCmd))
cmd_tree = ast.fix_missing_locations(SwitchInput().visit(ast.parse(inspect.getsource(cmd.Cmd)))) #get a version that swaps all input(...) calls with self.input_method(...)

#find the cmdloop function
found = False
for node in ast.walk(cmd_tree):
    if isinstance(node,ast.FunctionDef) and node.name == 'cmdloop':
        cmdloop_node = node
        found = True
        break
assert(found)

#find the PTCmd class
found = False
for node in ast.walk(ptcmd_tree):
    if isinstance(node,ast.ClassDef) and node.name == 'PTCmd':
        found = True
        ptcmd_node = node
        break
assert(found)
#add the cmdloop function to the class definition (overwrite inherited version)
ptcmd_node.body.append(cmdloop_node)
ptcmd_tree = ast.fix_missing_locations(ptcmd_tree)

#Redefine the new class
exec(compile(ptcmd_tree,'<ast>','exec'))

