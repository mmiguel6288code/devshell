# doctestify

doctestify is a tool to make it easier to make doctests.
Doctests are snippets of text that resemble a Python interactive mode session.
Doctests can be embedded in the docstrings within your code in order to serve two purposes:

1. To provide executable examples to users so they can better understand how to use your code

2. To support automated testing by running these lines and confirming the expected outputs are produced


A docstring is a block of inline text within your code at the start of a module, class, or function to document the function. When the builtin help() function is called on an object, the docstrings for that object's class and methods are displayed. Additionally there are a number of tools, such as sphinx or pdoc that generate polished documentation files by scanning docstrings within a project.

This module makes it as easy as possible to make doctests.

1. First decide what target item (package, module, class, or function) you want to make a doctest for. Identify the fully qualified name of that item:

    For a package or module, this is what you would put after the import keyword to import that package or module.
    For a class or function, this is how you would reference that class or function after importing its module:

    Example fully qualified names for different types of targets:
    ```
         import mypackage.mymodule;
         target_package = mypackage
         target_module = mypackage.mymodule
         target_class = mypackage.mymodule.myclass
         target_method = mypackage.mymodule.myclass.mymethod
         target_function = mypackage.mymodule.myfunction
    ```

2. In a shell or command line terminal, navigate to the folder containing the package or module, then run doctestify with the fully qualified name of the target:

    python -m doctestify mypackage.mymodule.myclass.mymethod

3. This will enter into interactive mode with all objects already imported from the the module containing the target
    ```
        >>> from mypackage.mymodule import *
        >>>
    ```


    In interactive mode, you now type all the commands you want to be included in doctests.
    The inputs you type, as well as everything that is printed to stdout will be collected by doctestify.
    You can press Ctrl+D to leave the interpreter when you are done.
    At this point, the doctests you just created will be added to the docstring of the target object.


To ensure the doctest insertion process works, the doctests for the module are run before and after this process.
The doctests in the updated module should produce no more errors than existed before the updates.
If there is any issues, the original code will be restored and the updated code will be saved in a separate file ending with ".failed_doctest_insert"

