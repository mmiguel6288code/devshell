import os, pkgutil, os.path, readline, inspect, doctest, sys, re, importlib, pdb, traceback, code, subprocess, shutil,textwrap, argparse, shlex
from contextlib import contextmanager
from cmd import Cmd
from pypager.pager import Pager
from pypager.source import StringSource
from io import StringIO
from .injector import doctestify, get_target, get_ast_obj
from . import __version__


@contextmanager
def capture_stdout():
    s = StringIO()
    sys.stdout = s
    yield s
    sys.stdout = sys.__stdout__
   
def run_cmd(cmd,do_paginate=False,print_also=False):
    print('Running command:\n  '+' '.join(cmd))
    if not do_paginate:
        subprocess.run(cmd)
    else:
        proc = subprocess.run(cmd,stdout=subprocess.PIPE)
        text = proc.stdout.decode('utf-8','replace')
        paginate(text,print_also=print_also)

def run_coverage(sourcedir,arglist,sourcefilename=None):
    if sourcefilename is None:
        cmd1 = [sys.executable,'-m','coverage','run','--source='+os.path.abspath(sourcedir),'--parallel-mode','-m','pytest','--doctest-modules',os.path.abspath(sourcedir)]+arglist
    else:
        cmd1 = [sys.executable,'-m','coverage','run','--source='+os.path.abspath(sourcedir),'--include="'+sourcefilename+'"','--parallel-mode','-m','pytest','--doctest-modules',os.path.abspath(os.path.join(sourcedir,sourcefilename))]+arglist
    cmd2 = [sys.executable,'-m','coverage','combine']
    cmd3 = [sys.executable,'-m','coverage','report','-m']
    cmd4 = [sys.executable,'-m','coverage','erase']
    run_cmd(cmd1)
    run_cmd(cmd2)
    run_cmd(cmd3,do_paginate=True,print_also=True)
    run_cmd(cmd4)

def paginate(text,print_also=False):
    p=Pager()
    p.add_source(StringSource(text,lexer=None))
    p.run()
    if print_also:
        print(text)

def _get_args_kwargs(*args,**kwargs):
    return args,kwargs
def _auto_debug_handler(exc_type,exc_value,exc_traceback):
    traceback.print_exception(exc_type,exc_value,exc_traceback)
    pdb.post_mortem(exc_traceback)
_default_excepthook = sys.excepthook


class DevshellCmd(Cmd,object):
    """
    This implements the command line interface for devshell
    """
    prompt = '(devshell)$ '
    intro = 'devshell version %s\nWelcome to devshell. Type help or ? to list commands. Start a line with ! to execute a shell command in a sub-shell (does not retain environmental variables).\n' % __version__
    _cdable = set(['package','module','class','root'])
    _callable = set(['function','method','coroutine','class'])

    

    def _ls(self,args=''):
        args = args.strip()
        if args != '':
            orig_cwd = self.cwd
            orig_pwd = list(self.pwd)
            self._ls_cache = None
            self.do_cd(args)
            result = self._ls('')
            self.cwd = orig_cwd
            os.chdir(orig_cwd)
            self.pwd = orig_pwd
            self._ls_cache = None
            return result
        else:
            if self._ls_cache is not None:
                return self._ls_cache
            if len(self.pwd) == 0:
                self._ls_cache = [((mi[1],'package') if mi[2] else (mi[1],'module')) for mi in sorted(pkgutil.iter_modules([self.cwd,os.path.join(self.cwd,'src')]),key=lambda mi: mi[1]) if (mi[1],mi[2]) != ('setup',False)]
                return self._ls_cache
            else:
                current_name,current_type = self.pwd[-1]
                if current_type == 'package':

                    self._ls_cache = [((mi[1],'package') if mi[2] else (mi[1],'module')) for mi in sorted(pkgutil.iter_modules([os.path.join(self.cwd,*[item[0] for item in self.pwd])]),key=lambda mi: mi[1])]
                    package_fqn = '.'.join(item[0] for item in self.pwd)
                    cwd = os.getcwd()
                    if not cwd in sys.path:
                        sys.path.insert(0,cwd)
                    try:
                        pkg = __import__(package_fqn)
                    except:
                        print('Could not fully import package: %s' % package_fqn)
                        print(textwrap.indent(traceback.format_exc(),'    '))
                        return

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
                    try:
                        mod = __import__(module_fqn)
                    except:
                        print('Could not import module: %s' % module_fqn)
                        print(textwrap.indent(traceback.format_exc(),'    '))
                        return
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
        super(DevshellCmd,self).__init__(*args,**kwargs)
    def do_h(self,args):
        """ Alias for help """
        self.do_help(args)
    def default(self,line):
        if line.startswith('!'):
            line = line[1:]
        os.system(line)
    def do_pip(self,args):
        """
    Help: (devshell)$ pip command [args...]

        Runs pip
        """
        arglist = [arg.strip() for arg in args.split() if arg.strip() != '']
        run_cmd([sys.executable,'-m','pip']+arglist)
    def do_restart(self,args):
        """
    Help: (devshell)$ restart

        Restarts devshell at the current working directory with the current path
        Sometimes needed to cleanly re-import scripts that were already imported and then changed.
        """
        sys.exit(subprocess.run([sys.executable,'-m','devshell','-d',os.path.abspath(os.getcwd()),'-t','.'.join([item[0] for item in self.pwd])]).returncode)


    def do_read(self,args):
        """
    Help: (devshell)$ read filename
        Opens the selected file in a paginated view (similar to Unix "less" or "more" commands)
        The preferred locale encoding defined by locale.getpreferredencoding() is used
        """
        with open(args,'r') as f:
            text = f.read()
        paginate(text)



    def do_mkdir(self,args):
        """
    Help: (devshell)$ mkdir dirname
        Creates the specified directory 
        """
        os.mkdir(args)
    def do_rm(self,args):
        """
    Help: (devshell)$ rm filename
        Deletes the file specified by filename. Will not delete a directory.
        See rmtree to delete a directory
        """
        os.remove(args)
    def do_rmtree(self,args):
        """
    Help: (devshell)$ rmtree dirname
        Deletes the directory specified by dirname and all of its contents.
        See rm to delete a single file
        """
        shutil.rmtree(args)

    def do_mv(self,args):
        """
    Help: (devshell)$ mv source target
        Moves the file or folder at source to target
        """
        try:
            src,dst = args.split()
        except:
            print('Invalid syntax')
            return
        shutil.move(src,dst)
    def do_cp(self,args):
        """
    Help: (devshell)$ cp source target
        Copies the file or folder at source to target
        """
        try:
            src,dst = args.split()
        except:
            print('Invalid syntax')
            return
        if os.path.isdir(src):
            shutil.copytree(src,dst)
        else:
            shutil.copy(src,dst)


    def do_run(self,args):
        """
    Help: (devshell)$ run shellcmd [args...]
        Runs the given command in a subshell
        """
        os.system(args)



    def do_edit(self,args):
        """
    Help: (devshell)$ edit editor
        Runs the command editor, passing the file of the currently targeted object in as first argument.
        If no editor is specified, an error message will apppear.
        For most editors (e.g. vim, nano, etc), this will open the file for editing.
        If the current item is package, opens __init__.py.

        For editors that have some other command line invocation, see the devshell run command.
        """
        editor = args.strip()
        if len(editor) == 0:
            print('Specify an editor (e.g. vim, nano, notepad++.exe, etc)')
            return
        else:
            editor=[editor]
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            current_name,current_type = self.pwd[-1]
            if current_type == 'package':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.')) + '/__init__.py')
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:
                    run_cmd(editor+[filepath])
            elif current_type == 'module':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.'))+'.py')
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:
                    run_cmd(editor+[filepath])
            else:
                try:
                    obj,mod,mod_fqn = get_target(target_fqn)
                except:
                    print('Failed to get target: %s' % target_fqn)
                    return
                filepath = inspect.getsourcefile(obj)
                print('File:',filepath)
                run_cmd(editor+[filepath])
        else:
            print('No target identified')
    def do_editvim(self,args):
        """
    Help: (devshell)$ editvim
        Opens vim to the first source line of the given target
        If on windows, opens gvim instead.
        """
        if sys.platform == 'win32' or sys.platform == 'cygwin':
            editor=['gvim']
        else:
            editor=['vim']
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            current_name,current_type = self.pwd[-1]
            if current_type == 'package':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.')) + '/__init__.py')
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:

                    run_cmd(editor+[filepath])
            elif current_type == 'module':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.'))+'.py')
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:
                    run_cmd(editor+[filepath])
            else:
                #try:
                if 1:
                    obj,mod,mod_fqn = get_target(target_fqn)
                    ast_obj,filepath,source = get_ast_obj(target_fqn,obj,mod,mod_fqn)
                    lineno = ast_obj.lineno
                #except:
                if 0:
                    print('Failed to get target: %s' % target_fqn)
                    return
                print('File:',filepath,'Line:',str(lineno))
                run_cmd(editor+[filepath,'+'+str(lineno)])
        else:
            print('No target identified')



    def do_debug(self,args):
        """
    Help: (devshell)$ debug(arg1,arg2,...,kwarg1=kwvalue1,kwarg2=kwvalue2,...)
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
                try:
                    result = pdb.runcall(obj,*pargs,**kwargs)
                    print('Return value: %s' % repr(result))
                except:
                    traceback.print_exc()
            else:
                if len(args) > 0:
                    print('No arguments are excepted for object type %s' % obj_type)
                else:
                    os.system('%s -m pdb %s' % (sys.executable,os.path.abspath(inspect.getsourcefile(obj))))

        else:
            print('No target identified')


    def do_listdir(self,args):
        """
    Help: (devshell)$ listdir path
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
    Help: (devshell)$ chdir path
        This changes the operating system folder path (current working directory) where devshell will look for packages and modules
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
    Help: (devshell)$ doctestify
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
    Help: (devshell)$ quit
        Exit the devshell shell.
        """
        print('Exiting devshell shell...')
        return True
    def do_exit(self,args):
        """
    Help:(devshell)$ exit
        Exit the devshell shell.
        """
        return self.do_quit(args)
    def do_q(self,args):
        """
    Help:(devshell)$ q 
        Exit the devshell shell.
        """
        return self.do_quit(args)
    def do_EOF(self,args):
        """
    Help: EOF
        Pressing Ctrl+D while in the devshell shell will result in exiting the devshell shell.
        Note that Ctrl+D is also used to terminate an interactive recording session and return to the devshell shell.
        """
        return self.do_quit(args)
    def do_doctest(self,args):
        """
    Help: (devshell)$ doctest [verbose]
        This runs the current doctests for the currently targeted item. verbose can be True or False. If unspecified, verbose=False.
        """
        if len(self.pwd) == 0:
            print('No target identified')
            return
        current_type = self.pwd[-1][1]
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            try:
                obj,mod,mod_fqn = get_target(target_fqn)
            except:
                print('Failed to get target: %s' % target_fqn)
                return
            if len(args.strip()) > 0:
                verbose = eval(args)
            else:
                verbose = False

            try:
                stdout_capture = StringIO()
                sys.stdout = stdout_capture
                
                if current_type in self._callable:
                    importlib.reload(mod)
                    importlib.reload(sys.modules[obj.__module__])
                    doctest.run_docstring_examples(obj,sys.modules[obj.__module__].__dict__,verbose)
                elif current_type in ['package','module']:
                    importlib.reload(mod)
                    importlib.reload(obj)
                    doctest.testmod(obj,verbose=verbose)
                else:
                    sys.stdout = sys.__stdout__
                    print('Invalid type to run doctest: %s' % current_type)
                    return
                sys.stdout = sys.__stdout__
                results = stdout_capture.getvalue()
                if len(results) != 0:
                    paginate(results)
                else:
                    print('All doctests passed')
            except:
                sys.stdout = sys.__stdout__
                traceback.print_exc()
        else:
            print('No target identified')
    def do_pytest(self,args):
        """
    Help: (devshell)$ pytest [pytest_args]
        This runs the pytest against the currently targeted item. 
        If pytest is not installed, an error message will be printed.

        The --doctest-modules option is automatically inserted.

        pytest_args are defined in the pytest documentation:
            https://docs.pytest.org/en/latest/usage.html
            See --pdb, --trace, --capture

        If there is no currently targeted item, pytest will be run against the folder indicated by getcwd:
            (devshell)$ pytest -ra --doctest-modules
                is equivalent to:
                    python -m pytest . -ra --doctest-modules

        If there is a target item, pytest will be run specifically against that item.
            For example, if the currently target object is mypackage.my_module.MyClass.my_test_method, then running 
            (devshell)$ pytest -ra
                is equivalent to:
                    python -m pytest  /fullpathto/mypackage/my_module.py::MyClass::my_test_method --doctest-modules -ra
        """
        try:
            import pytest
        except:
            print('pytest is not installed')
            return


        arglist = [arg.strip() for arg in args.split() if arg.strip() != '']
        if len(self.pwd) == 0:
            run_cmd([sys.executable,'-m','pytest',os.path.abspath(self.cwd),'--doctest-modules']+arglist)
            return
        current_type = self.pwd[-1][1]

        item_names = []
        reached_module = False
        item_names_inside_module = []
        for item_name,item_type in self.pwd:
            item_names.append(item_name)
            if reached_module:
                item_names_inside_module.append(item_name)
            if item_type == 'module':
                reached_module = True
        target_fqn = '.'.join(item_names)
        if target_fqn != '':
            try:
                obj,mod,mod_fqn = get_target(target_fqn)
            except:
                sys.stdout = sys.__stdout__
                #results = stdout_capture.getvalue()
                print('Failed to get target: %s' % target_fqn)
                return
            sourcefile = inspect.getsourcefile(obj)
            if current_type == 'package':
                sourcefile = os.path.dirname(sourcefile)
            pytest_node_id = '::'.join([os.path.abspath(sourcefile)]+item_names_inside_module)
            run_cmd([sys.executable,'-m','pytest',pytest_node_id,'--doctest-modules']+arglist)
        else:
            run_cmd([sys.executable,'-m','pytest',os.path.abspath(self.cwd),'--doctest-modules']+arglist)

    def do_coverage(self,args):
        """
    Help: (devshell)$ coverage [pytest_args]
        This runs coverage and pytest against the source file containing the currently targeted item. 
        This does not use the pytest-cov plugin, just the coverage and pytest packages themselves.
        If pytest and/or coverage are not installed, an error message will be printed.

        The --doctest-modules pytest argument is automatically inserted.

        pytest_args are defined in the pytest documentation:
            https://docs.pytest.org/en/latest/usage.html
            See --pdb, --trace, --capture

        If there is no currently targeted item, coverage and pytest will be run against the folder indicated by getcwd:
            (devshell)$ coverage -ra
                is functionally equivalent to:
                    python -m coverage run --parallel-mode --source=. pytest . -ra --doctest-modules
                    python -m coverage report -m

        If there is a target item, coverage and pytest will be run specifically against the entire source file containing that item.
            For example, if the currently target object is mypackage.my_module.MyClass.my_test_method, then running 
            (devshell)$ coverage -ra
                is functionally equivalent to:
                    python -m coverage run --parallel-mode --source=/fullpathto/mypackage --include=my_module.py pytest  /fullpathto/mypackage/my_module.py -ra --doctest-modules
                    python -m coverage report -m
        """
        try:
            import coverage
        except ImportError:
            print('coverage is not installed')
            return
        try:
            import pytest
        except ImportError:
            print('pytest is not installed')
            return
        arglist = [arg.strip() for arg in args.split() if arg.strip() != '']
        if len(self.pwd) == 0:
            run_coverage(self.cwd,arglist)
            return
        current_type = self.pwd[-1][1]
        item_names = []
        reached_module = False
        item_names_inside_module = []
        for item_name,item_type in self.pwd:
            item_names.append(item_name)
            if reached_module:
                item_names_inside_module.append(item_name)
            if item_type == 'module':
                reached_module = True
        target_fqn = '.'.join(item_names)
        if target_fqn != '':
            try:
                obj,mod,mod_fqn = get_target(target_fqn)
            except:
                sys.stdout = sys.__stdout__
                #results = stdout_capture.getvalue()
                print('Failed to get target: %s' % target_fqn)
                return
            sourcefile = inspect.getsourcefile(obj)
            sourcefilename = os.path.basename(sourcefile)
            sourcedir = os.path.dirname(sourcefile)
            run_coverage(sourcedir,arglist,sourcefilename)
        else:
            run_coverage(self.cwd,arglist)
    def do_source(self,args):
        """
    Help: (devshell)$ source
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
                        paginate(f.read())
            elif current_type == 'module':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.'))+'.py')
                if os.path.getsize(filepath) == 0:
                    print('File is empty')
                else:
                    with open(filepath,'r') as f:
                        paginate(f.read())
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
                    paginate(inspect.getsource(obj))
        else:
            print('No target identified')
    def do_grep(self,args):
        """
    Help: (devshell)$ grep pattern [OPTIONS]
        Searches the source code of the currently targeted item based on the provided regular expression.
        The source is split into lines and the regular expression is applied to each line.
        Files are opened for reading in string mode with errors being handled via open()'s errors='backslashreplace' option
        Regular expressions are according to python interpretation (not standard grep).
        Only includes python source files (.py$|.py[w3wxi]$|.pxd$)
        If a package is selected, all files will be looked at.
        If a module is selected, the module will be looked at.
        If a sub-module item is selected, only that items source code will be looked at.

        Supported options:
            -i = Ignore case (re.IGNORECASE)
                Normally, matching is case sensitive
                With -i specified, matching is case-insensitive

            -v = Invert match
                Normally, lines that match the pattern are included
                With -v, lines that do not match the pattern are included
            -p = Print to console after displaying
                Normally, the results will be paginated in a page viewer (similar to unix less)
                With -p, the results will be paginated and then printed to the console after
                
        """
        target_fqn = '.'.join(item[0] for item in self.pwd)
        if target_fqn != '':
            current_name,current_type = self.pwd[-1]
            if current_type == 'package':
                #recurse through package directory
                path = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.')))
                grep(args,path=path)
                
            elif current_type == 'module':
                filepath = os.path.abspath(os.path.join(self.cwd,*target_fqn.split('.'))+'.py')
                grep(args,path=filepath)
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
                    grep(args,source=inspect.getsource(obj),path=filepath)
        else:
            path = os.path.abspath(os.getcwd())
            grep(args,path=path)

    def do_doc(self,args):
        """
    Help: (devshell)$ doc
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
            result = ('    '+'\n    '.join(lines))
            if len(result.strip()) != 0:
                paginate(result,print_also=True)
            else:
                print('No documentation exists for the given target')
        else:
            print('No target identified')
        

    def do_getcwd(self,args):
        """
    Help: (devshell)$ getcwd
        This displays the operating system folder path (current working directory) where devshell will look for packages and modules
        """
        print(self.cwd)
    def do_ls(self,args):
        """
    Help: (devshell)$ ls [python_object]
        This will show all items contained within the currently targeted item.
            e.g. for a package, this would list the modules
            e.g. for a module, this would list the functions and classes
            etc
        If there is no currently targeted item, then all packages in the current working directory or within a subfolder of the current working directory named "src" will be shown.
        Note that using this command may result in importing the module containing the currently targeted item.
        Note that setup.py files will be purposefully excluded because importing/inspecting them without providing commands results in terminating python.

        For tab completion, use the dot "." character to separate python items, not the slash "/" character.

        This is NOT the same as the usual interpretation of ls in other shells.
        For the usual interpretation, see listdir.
        """
        lines = []
        result = self._ls(args)
        if result is None:
            return
        for item_name,item_type in result: 
            if item_type in self._cdable:
                if len(self.pwd) == 0 and item_type == 'package' and not os.path.exists(os.path.join(self.cwd,item_name,'__init__.py')) and os.path.exists(os.path.join(self.cwd,'src',item_name,'__init__.py')):
                    lines.append('    %s%sdirectory (./src)' % (item_name.ljust(30), item_type.ljust(30)))
                else:
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
    Help: (devshell)$ pwd
        This shows the fully qualified name of the currently targeted item.

        This is NOT the same as the usual interpretation of pwd in other shells.
        For the usual interpretation, see getcwd.
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
            if len(self.pwd) > 0:
                last_item,last_item_type = self.pwd.pop()
                if len(self.pwd) == 0 and last_item_type == 'package' and os.path.basename(self.cwd) == 'src' and os.path.exists(os.path.join(self.cwd,last_item,'__init__.py')) and not os.path.exists(os.path.join(self.cwd,'..',last_item,'__init__.py')):
                    self.do_chdir('..')

            resolved = True
            clear_ls_cache = True
            #go up if in src
        elif args == '/':
            del self.pwd[:]
            resolved = True
            clear_ls_cache = True
        elif '.' not in args:
            for item,item_type in self._ls():
                if item == args:
                    if len(self.pwd) == 0 and item_type == 'package' and not os.path.exists(os.path.join(self.cwd,item,'__init__.py')) and os.path.exists(os.path.join(self.cwd,'src',item,'__init__.py')):
                        self.do_chdir('src')
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
    def do_interactive(self,args):
        """
    Help: (devshell)$ interactive
        Opens a python interactive session
        """
        console = code.InteractiveConsole()
        console.interact()
    def do_python(self,args):
        """
    Help: (devshell)$ python
        Opens a python interactive session
        """
        self.do_interactive(args)

    def do_cd(self,args):
        """
    Help: (devshell)$ cd <argument>
        This changes the currently targeted item.
        
        <argument> can be part of a fully qualified name to append to the end of the current target.

        If there is no current target, then one may cd into a package within the current working directory or within a package in a subfolder of the current working directory named "src".
        Cding into the "src" subfolder only occurs when the src subfolder has the package with the given name and the current working directory does not.
        Cding into the "src" subfolder will change the current working directory to be the "src" subfolder.
        Command completion is supported via the tab key.
        Note that performing command line completion at a level may result in importing/loading the module containing the item being examined.

        The following are special invocations:

            (devshell)$ cd /
                This will remove all parts of the current fully qualified name

            (devshell)$ cd .
                This has no effect

            (devshell)$ cd ..
                This removes the last piece of the currently fully qualified name (navigates up to the parent item)
                If leaving a package to a subfolder named "src", will also change the current working directory to be the parent directory of "src" if a package with the current target as its name exists only in the "src" directory and not in the parent directory.

        This is NOT the same as the usual interpretation of cd in other shells.
        For the usual interpretation, see chdir.
        
        """
        resolved,clear_ls_cache = self._cd(args)
        if not resolved is True:
            print('Error - "%s" does not exist' % args)
        #else:
        #    self.prompt = '(devshell)%s$ ' % self._pwd()
        if clear_ls_cache:
            self._ls_cache = None
    def complete_cd(self,text,line,begin_idx,end_idx):
        return self._complete_python(text,line,begin_idx,end_idx)
    def complete_ls(self,text,line,begin_idx,end_idx):
        return self._complete_python(text,line,begin_idx,end_idx)
    def _complete_python(self,text,line,begin_idx,end_idx):
        orig_cwd = self.cwd
        if '.' not in text:
            results = [item[0] for item in self._ls() if item[0].startswith(text)]
            if self.cwd != orig_cwd:
                self.cwd = orig_cwd
                os.chdir(orig_cwd)
            return results

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
            if self.cwd != orig_cwd:
                self.cwd = orig_cwd
                os.chdir(orig_cwd)
            return results
    def complete_chdir(self,text,line,begin_idx,end_idx):
        return self._complete_dirs('chdir',text,line,begin_idx,end_idx)

    def complete_listdir(self,text,line,begin_idx,end_idx):
        return self._complete_dirs('listdir',text,line,begin_idx,end_idx)

    def complete_rmtree(self,text,line,begin_idx,end_idx):
        return self._complete_dirs('rmtree',text,line,begin_idx,end_idx)
    
    def complete_rm(self,text,line,begin_idx,end_idx):
        return self._complete_files('rm',text,line,begin_idx,end_idx)

    def complete_cp(self,text,line,begin_idx,end_idx):
        return self._complete_lastdirfile('cp',text,line,begin_idx,end_idx)
    def complete_mv(self,text,line,begin_idx,end_idx):
        return self._complete_lastdirfile('mv',text,line,begin_idx,end_idx)
    def complete_read(self,text,line,begin_idx,end_idx):
        return self._complete_files('read',text,line,begin_idx,end_idx)
    def complete_run(self,text,line,begin_idx,end_idx):
        return self._complete_lastdirfile('run',text,line,begin_idx,end_idx)
    def completedefault(self,text,line,begin_idx,end_idx):
        return self._complete_lastdirfile(None,text,line,begin_idx,end_idx)

    def _complete_dirs(self,cmd,text,line,begin_idx,end_idx):
        path = re.sub('^\\s*%s\\s*'%cmd,'',line)
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

    def _complete_files(self,cmd,text,line,begin_idx,end_idx):
        path = re.sub('^\\s*%s\\s*'%cmd,'',line)
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
        return [item for item in os.listdir(front) if item.startswith(last_piece) and not os.path.isdir(os.path.join(front,item))]
    def _complete_lastdirfile(self,cmd,text,line,begin_idx,end_idx):
        if cmd is not None:
            paths = re.sub('^\\s*%s\\s*'%cmd,'',line)
        else:
            paths = line
        qc = len(re.findall('(?<!\\\\)"',paths))
        if qc > 0:
            #non-escaped quotes found

            #get the position of the right-most non-escaped quote
            rq_pos = len(paths) - 1 - re.search('"(?!\\\\)',paths[::-1]).start(0)
            if qc % 2 == 0:
                #there are an even number of quotes i.e. we are outside of any quoted argument
                path = paths[rq_pos+1:].strip()

            else:
                #there are an odd number of quotes i.e. we are in the middle of a quoted argument
                path = paths[rq_pos+1:]
        else:
            rs_match = re.search(' (?!\\\\)',paths[::-1])
            if rs_match is not None:
                #there are non-escaped spaces
                rs_pos = len(paths) - 1 - rs_match.start(0)
                path = paths[rs_pos+1:].strip()
            else:
                #there are no spaces
                path = paths
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
        return [item for item in os.listdir(front) if item.startswith(last_piece)]

def grep(args,source=None,path=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('pattern')
    parser.add_argument('-i',action='store_true')
    parser.add_argument('-v',action='store_true')
    parser.add_argument('-p',action='store_true')
    parsed_args = parser.parse_args(shlex.split(args))


    flags = (re.I if parsed_args.i else 0)
    invert_match = parsed_args.v

    regex = re.compile(parsed_args.pattern,flags)
    if source is None:
        def sourcegen_func():
            if os.path.isdir(path):
                #recurse
                pathgen = ((os.path.join(dirpath,filename) for filename in filenames) for dirpath,dirnames,filenames in os.walk(path))
            else:
                pathgen = ((path for _ in [None]) for _ in [None])
            for filegen in pathgen:
                for filepath in filegen:
                    if re.search('^\\.(py|py[w3wxi]|pxd)$',os.path.splitext(filepath)[1]) is not None:
                        with open(filepath,'r',errors='backslashreplace') as f:
                            source = f.read()
                        yield (source,filepath)
        sourcegen = sourcegen_func()
    else:
        sourcegen = ((source,path) for _ in [None])
    output_lines = []
    for source,path in sourcegen:
        filename = os.path.basename(path)
        for line_i,line in enumerate(source.splitlines()):
            matched = regex.search(line) is not None
            include = matched ^ invert_match
            if include:
                output_lines.append(':'.join([filename,str(line_i),line]))
    results = '\n'.join(output_lines)
    paginate(results)
    if parsed_args.p:
        print(results)
    return results








