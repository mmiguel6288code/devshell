import os, pkgutil, os.path, readline, inspect, doctest, sys, re, importlib, pdb
from cmd import Cmd
from .core import doctestify, get_target

def _get_args_kwargs(*args,**kwargs):
    return args,kwargs

class DoctestifyCmd(Cmd,object):
    """
    This implements the command line interface for doctestify
    """
    prompt = '(doctestify)$ '
    intro = 'Welcome to the doctestify shell. Type help or ? to list commands.\n'
    _cdable = set(['package','module','class','root'])
    _callable = set(['function','method','coroutine','class'])

    

    def _ls(self):
        if self._ls_cache is not None:
            return self._ls_cache
        if len(self.pwd) == 0:
            self._ls_cache = [((mi[1],'package') if mi[2] else (mi[1],'module')) for mi in sorted(pkgutil.iter_modules([self.cwd]),key=lambda mi: mi[1]) if (mi[1],mi[2]) != ('setup',False)]
            return self._ls_cache
        else:
            current_name,current_type = self.pwd[-1]
            if current_type == 'package':

                self._ls_cache = [((mi[1],'package') if mi[2] else (mi[1],'module')) for mi in sorted(pkgutil.iter_modules([os.path.join(self.cwd,*[item[0] for item in self.pwd])]),key=lambda mi: mi[1])]
                package_fqn = '.'.join(item[0] for item in self.pwd)
                pkg = __import__(package_fqn)
                for item in self.pwd[1:]:
                    pkg = getattr(pkg,item[0])
                for item_name,item in pkg.__dict__.items():
                    if inspect.getmodule(item) != pkg:
                        continue
                    if inspect.isfunction(item):
                        self._ls_cache.append((item_name,'function'))
                    elif hasattr(inspect,'iscoroutinefunction') and inspect.iscoroutinefunction(item):
                        self._ls_cache.append((item_name,'coroutine'))
                    elif inspect.isclass(item):
                        self._ls_cache.append((item_name,'class'))
                self._ls_cache.sort()
                return self._ls_cache

            elif current_type == 'module':
                module_fqn = '.'.join(item[0] for item in self.pwd)
                mod = __import__(module_fqn)
                for item in self.pwd[1:]:
                    mod = getattr(mod,item[0])
                self._ls_cache = []
                for item_name,item in mod.__dict__.items():
                    if inspect.getmodule(item) != mod:
                        continue
                    if inspect.isfunction(item):
                        self._ls_cache.append((item_name,'function'))
                    elif hasattr(inspect,'iscoroutinefunction') and inspect.iscoroutinefunction(item):
                        self._ls_cache.append((item_name,'coroutine'))
                    elif inspect.isclass(item):
                        self._ls_cache.append((item_name,'class'))
                self._ls_cache.sort()
                return self._ls_cache
            elif current_type == 'class':
                klass_fqn = '.'.join(item[0] for item in self.pwd)
                try:
                    klass,_,_ = get_target(klass_fqn)
                except:
                    print('Failed to get target: %s' % klass_fqn)
                    return

                self._ls_cache = []
                for item_name,item in klass.__dict__.items():
                    if inspect.ismethod(item):
                        self._ls_cache.append((item_name,'method'))
                    elif inspect.isfunction(item):
                        self._ls_cache.append((item_name,'function'))
                    elif hasattr(inspect,'iscoroutinefunction') and inspect.iscoroutinefunction(item):
                        self._ls_cache.append((item_name,'coroutine'))
                    elif inspect.isclass(item):
                        self._ls_cache.append((item_name,'class'))
                self._ls_cache.sort()
                return self._ls_cache
            else:
                print('Error - cannot perform ls when targeting a %s - try to run "cd .." first' % current_type)
                return []

    def __init__(self,*args,**kwargs):
        self.cwd = os.getcwd()
        self.pwd = []
        self._ls_cache = None
        super(DoctestifyCmd,self).__init__(*args,**kwargs)
    def do_h(self,args):
        """ Alias for help """
        self.do_help(args)

    def do_debug(self,args):
        """
    Help: (doctestify)$ debug(arg1,arg2,...,kwarg1=kwvalue1,kwarg2=kwvalue2,...)
        If currently targeting a class or function, this will attempt to load and call that code with the provided positional args and keyword args - entering pdb debug mode on the first line. 
        If currently targeting a package or module, this will enter debug mode at the first line of the module as if the module's file were directly run with python -m pdb <filename>.
       """
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            try:
                obj,mod,mod_fqn = get_target(target_fqn)
            except:
                print('Failed to get target: %s' % target_fqn)
                return
            args = args.strip()
            obj_type = self.pwd[-1][1]
            if len(self.pwd) == 0:
                print('No target is selected')
                return

            if obj_type in self._callable:
                if len(args) > 0:
                    pargs,kwargs = eval('_get_args_kwargs{args}'.format(args=args),sys.modules[obj.__module__].__dict__,{'_get_args_kwargs':_get_args_kwargs})
                else:
                    pargs = tuple()
                    kwargs = {}
                result = pdb.runcall(obj,*pargs,**kwargs)
                print('Return value: %s' % repr(result))
            else:
                if len(args) > 0:
                    print('No arguments are excepted for object type %s' % obj_type)
                else:
                    os.system('%s -m pdb %s' % (sys.executable,os.path.abspath(inspect.getsourcefile(obj))))

        else:
            print('No target identified')


    def do_listdir(self,args):
        """
    Help: (doctestify)$ listdir path
        This lists the files/subfolders within the provided operating system folder path
        If path is not provided, then files/subfolders within the operating system folder path (current working directory) will be listed
        """
        if args == '':
            args = '.'
        if not os.path.exists(args):
            print('Error - path does not exist: %s' % args)
            return
        if not os.path.isdir(args):
            print('Error - path is not a folder: %s' % args)
            return
        lines = []
        for item in os.listdir(args):
            if os.path.isdir(item):
                itemtype = 'folder'
            else:
                itemtype = 'file'
            lines.append('    '+item.ljust(30)+itemtype)
        lines.sort()
        print('\n'.join(lines))



    def do_chdir(self,args):
        """
    Help: (doctestify)$ chdir path
        This changes the operating system folder path (current working directory) where doctestify will look for packages and modules
        """
        if os.path.exists(args) and os.path.isdir(args):
            os.chdir(args)
            self.cwd = os.getcwd()
            self.pwd = []
            self._ls_cache = None
        else:
            print('Error - path does not exist: %s' % args)

    def do_doctestify(self,args):
        """
    Help: (doctestify)$ doctestify
        Performs doctestify on the currently targeted item.
        This will cause an interactive python recording session to begin with all items from the targeted item's module imported in automatically.
        All inputs and outputs will be recorded and entered into the targeted item's docstring as a doctest.
        """
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            doctestify(target_fqn)
        else:
            print('No target identified')

    def do_quit(self,args):
        """
    Help: (doctestify)$ quit
        Exit the doctestify shell.
        """
        print('Exiting doctestify shell...')
        return True
    def do_EOF(self,args):
        """
    Help: EOF
        Pressing Ctrl+D while in the doctestify shell will result in exiting the doctestify shell.
        Note that Ctrl+D is also used to terminate an interactive recording session and return to the doctestify shell.
        """
        return self.do_quit(args)
    def do_doctest(self,args):
        """
    Help: (doctestify)$ doctest
        This runs the current doctests for the currently targeted item. Verbose mode is enabled.
        """
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            try:
                obj,mod,mod_fqn = get_target(target_fqn)
            except:
                print('Failed to get target: %s' % target_fqn)
                return

            importlib.reload(sys.modules[obj.__module__])
            doctest.run_docstring_examples(obj,sys.modules[obj.__module__].__dict__,True)
        else:
            print('No target identified')

    def do_source(self,args):
        """
    Help: (doctestify)$ source
        This displays the file name and source code for the currently targeted item.
        """
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            current_name,current_type = self.pwd[-1]
            if current_type == 'package':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.')) + '/__init__.py')
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:
                    with open(filepath,'r') as f:
                        print(f.read())
            elif current_type == 'module':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.'))+'.py')
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:
                    with open(filepath,'r') as f:
                        print(f.read())
            else:
                try:
                    obj,mod,mod_fqn = get_target(target_fqn)
                except:
                    print('Failed to get target: %s' % target_fqn)
                    return
                filepath = inspect.getsourcefile(obj)
                print('File:',filepath)
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:
                    print(inspect.getsource(obj))
        else:
            print('No target identified')
    def do_doc(self,args):
        """
    Help: (doctestify)$ doc
        This displays the docstring for the currently targeted item.
        """
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            try:
                obj,mod,mod_fqn = get_target(target_fqn)
            except:
                print('Failed to get target: %s' % target_fqn)
                return
            doc = inspect.getdoc(obj)
            lines = []
            if self.pwd[-1][1] in self._callable:
                lines.append(self.pwd[-1][1]+': '+self.pwd[-1][0] + str(inspect.signature(obj)))
            else:
                lines.append(self.pwd[-1][1]+': '+self.pwd[-1][0])
            if doc is not None:
                lines.append('"""')
                lines.append(re.sub('\n','\n    ',doc))
                lines.append('"""')
            else:
                lines.append('')
                lines.append('No docstring exists for target')
            print ('    '+'\n    '.join(lines))
        else:
            print('No target identified')
        

    def do_getcwd(self,args):
        """
    Help: (doctestify)$ getcwd
        This displays the operating system folder path (current working directory) where doctestify will look for packages and modules
        """
        print(self.cwd)
    def do_ls(self,args):
        """
    Help: (doctestify)$ ls
        This will show all items contained within the currently targeted item.
            e.g. for a package, this would list the modules
            e.g. for a module, this would list the functions and classes
            etc
        Note that using this command may result in importing the module containing the currently targeted item.
        Note that setup.py files will be purposefully excluded because importing/inspecting them without providing commands results in terminating python.
        """
        lines = []
        for item_name,item_type in self._ls():
            if item_type in self._cdable:
                lines.append('    %s%sdirectory' % (item_name.ljust(30), item_type.ljust(30)))
            else:
                lines.append('    %s%snon-directory' % (item_name.ljust(30), item_type.ljust(30)))
        print('\n'.join(lines))
    def _pwd(self):
        if len(self.pwd) > 0:
            return ('/'+'.'.join(item[0] for item in self.pwd),self.pwd[-1][1])
        else:
            return '/','root'
    def do_pwd(self,args):
        """
    Help: (doctestify)$ pwd
        This shows the fully qualified name of the currently targeted item.
        """
        pwd,current_type = self._pwd()
        print('%s (%s)' % (pwd.ljust(30),current_type))

    def _cd(self,args):
        resolved = False
        clear_ls_cache = False
        if args == '.':
            resolved = True
            clear_ls_cache = False
        elif args == '..':
            self.pwd.pop()
            resolved = True
            clear_ls_cache = True
        elif args == '/':
            del self.pwd[:]
            resolved = True
            clear_ls_cache = True
        elif '.' not in args:
            for item,item_type in self._ls():
                if item == args:
                    self.pwd.append((item,item_type))
                    resolved = True
                    clear_ls_cache = True
                    break
        else:
            pieces = args.split('.')
            orig_pwd = list(self.pwd)
            resolved = True
            clear_ls_cache = False
            orig_ls_cache = self._ls_cache
            for piece in pieces:
                self._ls_cache = None
                piece_resolved,piece_clear_ls_cache = self._cd(piece)
                if not piece_resolved:
                    resolved = False
                    self.pwd = orig_pwd
                    clear_ls_cache = False
                    break
                else:
                    clear_ls_cache = clear_ls_cache or piece_clear_ls_cache
            self._ls_cache = orig_ls_cache
        return (resolved,clear_ls_cache)

    def do_cd(self,args):
        """
    Help: (doctestify)$ cd <argument>
        This changes the currently targeted item.
        
        <argument> can be part of a fully qualified name to append to the end of the current target.
        Command completion is supported via the tab key.
        Note that performing command line completion at a level may result in importing/loading the module containing the item being examined.

        The following are special invocations:

            (doctestify)$ cd /
                This will remove all parts of the current fully qualified name

            (doctestify)$ cd .
                This has no effect

            (doctestify)$ cd ..
                This removes the last piece of the currently fully qualified name (navigates up to the parent item)
        
        """
        resolved,clear_ls_cache = self._cd(args)
        if not resolved is True:
            print('Error - "%s" does not exist' % args)
        #else:
        #    self.prompt = '(doctestify)%s$ ' % self._pwd()
        if clear_ls_cache:
            self._ls_cache = None
    def complete_cd(self,text,line,begin_idx,end_idx):
        if '.' not in text:
            return [item[0] for item in self._ls() if item[0].startswith(text)]
        else:
            orig_pwd = list(self.pwd)
            orig_ls_cache = self._ls_cache
            ts = text.split('.')
            front = '.'.join(ts[:-1])
            
            last_piece = ts[-1]
            resolved,clear_ls_cache = self._cd(front)
            if resolved:
                self._ls_cache = None
                results = [front+'.'+item[0] for item in self._ls() if item[0].startswith(last_piece)]
            else:
                results = []
            self.pwd = orig_pwd
            self._ls_cache = orig_ls_cache
            return results
    def complete_chdir(self,text,line,begin_idx,end_idx):
        path = re.sub('^\\s*chdir\\s*','',line)
        pieces = re.split('([/\\\\])',path)
        if len(pieces) > 1:
            front = ''.join(pieces[:-2])
            if front == '':
                front = '.'
            last_dlm = pieces[-2]
            last_piece = pieces[-1]
        else:
            front = '.'
            last_piece = path
        return [item for item in os.listdir(front) if item.startswith(last_piece) and os.path.isdir(os.path.join(front,item))]
    def complete_listdir(self,text,line,begin_idx,end_idx):
        path = re.sub('^\\s*listdir\\s*','',line)
        pieces = re.split('([/\\\\])',path)
        if len(pieces) > 1:
            front = ''.join(pieces[:-2])
            if front == '':
                front = '.'
            last_dlm = pieces[-2]
            last_piece = pieces[-1]
        else:
            front = '.'

            last_piece = path
        return [item for item in os.listdir(front) if item.startswith(last_piece) and os.path.isdir(os.path.join(front,item))]
        

        
