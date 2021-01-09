# devshell

[View API documentation](http://htmlpreview.github.io/?https://github.com/mmiguel6288code/devshell/blob/master/docs/devshell/index.html)

devshell provides the power user terminal python developer feeling.

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

That's nice, but what can you do besides inspecting what code blocks exist?

```bash
(devshell)$ help                                                                                                                                                                                  

Documented commands (type help <topic>):
========================================
EOF       create      doctestify  h            mv    pwd     read     source
activate  deactivate  edit        help         pcd   pytest  restart  venv  
cd        debug       editvim     interactive  pip   python  rm     
coverage  doc         exit        ls           pls   q       rmtree 
cp        doctest     grep        mkdir        ppwd  quit    run    
```

## What are doctests and why should I care?
Doctests are snippets of text that resemble a Python interactive mode session.
Doctests can be embedded in the docstrings within your code in order to serve two purposes:

1. To provide executable examples to users so they can better understand how to use your code

2. To support automated testing by running these lines and confirming the expected outputs are produced


A docstring is a block of inline text within your code at the start of a module, class, or function to document the function. When the builtin help() function is called on an object, the docstrings for that object's class and methods are displayed. Additionally there are a number of tools, such as sphinx or pdoc that generate polished documentation files by scanning docstrings within a project.

## How to use devshell
First open a shell or command line window and navigate to the folder containing the packages and/or modules of interest.
Then run:

    ```
    $ python -m devshell

    Starting devshell command line interface...
    Welcome to the devshell shell. Type help or ? to list commands.

    (devshell)$
    ```

You will then enter the devshell shell, which was designed to look and feel very similar to a unix shell.
The big difference is that instead of navigating through actual files/directories, the devshell shell navigates through python packages, modules, classes, and functions. Tab-completion is supported.

In the shell, you can type help to list all the commands.

    ```
    (devshell)$ help
    Documented commands (type help <topic>):
    ========================================
    EOF       cp       devshell  h            ls     pwd     quit    run   
    cd        debug    edit        help         mkdir  pytest  read    source
    chdir     doc      exit        interactive  mv     python  rm    
    coverage  doctest  getcwd      listdir      pip    q       rmtree
    ```

You can also type help followed by a command to get information about that particular command:

    ```
    (devshell)$ help ls

        Help: (devshell)$ ls
            This will show all items contained within the currently targeted item.
                e.g. for a package, this would list the modules
                e.g. for a module, this would list the functions and classes
                etc
            Note that using this command may result in importing the module containing the currently targeted item.
            Note that setup.py files will be purposefully excluded because importing/inspecting them without providing commands results in terminating python.k
    ```

Use the pwd, cd, and ls commands to navigate through different items:

    ```
    devshell)$ ls
        devshell          package             directory
        test_pkg            package             directory
        tests               package             directory
    (devshell)$ cd test_pkg
    (devshell)$ cd test_subpkg.test_mod.f
    (devshell)$ pwd
    /test_pkg.test_subpkg.test_mod.f
    ```

Once you are navigated to the item of interest, run the devshell command to enter a recorded interactive python session. All items from the containing module of the targeted item will automatically be imported. You essentially just type the doctest inputs, and the interactive session will evaluate them and display the outputs. When done, press Ctrl+D to exit the interactive session. At this point, devshell will write the recorded actions into the docstring of the targeted object. Afterwards, it will run doctests on that object to ensure there are no issues. If any issues are encountered, the original file will be restored and the problematic file will be saved with a special suffix in the same folder.

    ```
    (devshell)$ devshell
    Testing doctest execution of original file
    ...done: Fail count = 0, Total count = 0
    Entering interactive console
    Doctest insertion targeting object test_pkg.test_subpkg.test_mod.f within /home/mtm/interspace/devshell/test_pkg/test_subpkg/test_mod.py
    Press Ctrl+D to stop writing code and incorporate session into the docstring of the targeted object
    To abort this session without writing anything into the targeted file, call the exit() function
    >>> from test_pkg.test_subpkg.test_mod import * # automatic import by devshell
    >>> f(20)
    20
    >>>
    Writing doctest lines to file
    Testing doctest execution of new file
    ...done: Fail count = 0 (old=0), Total count = 1 (old=0)
    File successfully updated

    ```

You can use the doc or source commands to verify the doctest was written in:

    ```
    (devshell)$ doc
    >>> f(20)
    20

    (devshell)$ source
    File: /home/mtm/interspace/devshell/test_pkg/test_subpkg/test_mod.py
    def f(x):
    """
    >>> f(20)
    20
    """
    return x

    ```

You can also change the current working directory that the devshell shell is scanning for modules and packages with.
You can navigate the filestystem using chdir, listdir, and getcwd, which do the same things as the standard python os module methods of the same name.
Tab-completion is supported for chdir and listdir.

To exit the doctest shell, just press Ctrl+D or type the quit command.

