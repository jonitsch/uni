# IMPORTANT: When making change be sure to check exec_p2.py as well.

def exec_program(exec_str, exec_env, show_print):
    # Explicitly clear __builtins__: we don't want it to return to us
    # as a zombie; in other words, we don't want any of the builtins
    # to appear implicitly by not passing a __builtins__ dictionary
    # argument to "exec".
    exec_env["__builtins__"] = { "range" : range
                               , "print" : print if show_print else lambda arg, *args: None
                               }
    # Some notes: "range" is a class and "print" a function in Python
    # 3.x, so we can include both in builtins (in contrast to "print"
    # being a statement in Python 2.x).

    exec(exec_str, exec_env)
