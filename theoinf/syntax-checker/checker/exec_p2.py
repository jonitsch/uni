# IMPORTANT: When making change be sure to check exec_p3.py as well.

class DummyStdout(object):
    def write(self, what):
        # Ignore.
        pass

class HideStdout(object):
    def __init__(self, show_print):
        super(HideStdout, self).__init__()
        self.hide = not show_print

    def __enter__(self):
        if self.hide:
            import sys
            self.stdout = sys.stdout
            sys.stdout = DummyStdout()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.hide:
            import sys
            sys.stdout = self.stdout

def exec_program(exec_str, exec_env, show_print):
    # We cannot hide "print" in Python 2.x: it is a builtin statement
    # and not a function; thus we have to resort to "bending" default
    # sys.stdout to a dummy writer that does nothing. We have to make
    # sure that it gets restored even in case of an exception, that's
    # what the HideStdout class and the with statement below is for.

    # Explicitly clear __builtins__: we don't want it to return to us
    # as a zombie; in other words, we don't want any of the builtins
    # to appear implicitly by not passing a __builtins__ dictionary
    # argument to "exec".
    exec_env["__builtins__"] = { "range" : range
                               }

    # Some notes: "range" is a function in Python 2.x, while "print"
    # is a statement. So we need not include the latter in builtins.

    with HideStdout(show_print):
        exec exec_str in exec_env
