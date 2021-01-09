# devshell

[View API documentation](http://htmlpreview.github.io/?https://github.com/mmiguel6288code/devshell/blob/master/docs/devshell/index.html)

devshell is my python development workflow helper.

## Navigating Code Trees

There's normal basic shell navigation with cd, ls, pwd, and then there are python versions of those for navigating through a code tree: pcd, pls, ppwd.

What is a code tree? It is the following types of code blocks:

1. Package
2. Module
3. Class
4. Function/Method/Coroutine

```bash
$ cd ~/projects/statopy
$ ls
LICENSE  __pycache__  statopy.py
$ python3 -m devshell
Starting devshell command line interface...
devshell version 0.0.3
Welcome to devshell. Type help or ? to list commands. Start a line with ! to execute a shell command in a sub-shell (does not retain environmental variables).

(devshell)$                                                                                         
```
If a package or module in your current working directory (the normal type affected by cd and reported with pwd), then those will show up when you type pls.
You can enter your "python location" into it via pcd and check your current python location with ppwd.

Autocompletion works as usual for cd and ls.
For the python versions, autocompletion shows you what your options are in terms of child code blocks (e.g. methods in the current class).

```bash
(devshell)$ pls                                                                                                                                                                                   
    statopy                       module                        directory
(devshell)$ pcd statopy                                                                                                                                                                           
(devshell)$ pls                                                                                                                                                                                   
    ScalarProbModel               class                         directory
    ScalarRegression              class                         directory
    ScalarStats                   class                         directory
    VectorStats                   class                         directory
(devshell)$ pcd ScalarStats                                                                                                                                                                       
(devshell)$ pls                                                                                                                                                                                   
    __add__                       function                      non-directory
    __init__                      function                      non-directory
    __setattr__                   function                      non-directory
    consume                       function                      non-directory
    update                        function                      non-directory
(devshell)$ ppwd                                                                                                                                                                                  
/statopy.ScalarStats           (class)
(devshell)$  
```

## Commands

That's nice, but what can you do besides inspecting what code blocks exist?

Type help to see a list of commands. Calling programs with arguments/redirection works as usual.

```bash
(devshell)$ help                                                                                                                                                                                  

Documented commands (type help <topic>):
========================================
EOF       deactivate  edit     help         pcd   pytest  restart  venv
activate  debug       editvim  interactive  pip   python  rm     
cd        doc         exit     ls           pls   q       rmtree 
coverage  doctest     grep     mkdir        ppwd  quit    run    
cp        doctestify  h        mv           pwd   read    source 
```

## Doctests
If you navigate to a code block, you can examine the docstring and function definition using the ```doc ``` command.
You can run any doctests present in that code block by using the ```doctest ``` command.
You can call ```doctestify ``` to enter into an interactive session with the module's contents imported. All input and output in this session is recorded, and when the session is closed via CTRL+D, the input/output is appended to the docstring of the current code block as an additional set of doctests.

```doctestify resume ``` will open the interactive session and execute all existing doctest commands in the current docstring before turning interactive control over to you. This is useful if you are tweaking code while repeatedly running some test. You don't have to rewrite any setup code multiple times, just use what is in the docstring.

## Pytest/Coverage
```pytest``` and ```coverage``` - pretty self-explanatory. Coverage runs pytest and doctests and produces a combined report.

## Debugging
```debug(5,10)```  takes the current function or class and calls it like current_func(5,10), entering debug mode on the first line. You can put any python calling expression and as many arguments as you want.
If the current code block is a module or package, it requires no inputs, just call ```debug```. For a module, it will enter debug mode on the first line of the module. For a package, it will enter debug mode for the first line of the __init__.py file.


## Looking at code 
```grep pattern [OPTIONS]``` runs a grep-like function that is filtered on the current code block.

```editvim``` opens vim to the line corresponding to the currently targeted code block.

```source``` opens a paginated view with the text of the current code block (excludes the rest of the file).

