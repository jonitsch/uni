from .lexer import prepare, expand_lexpos
from .parser import Parser, ParseError
from .specification import check_common, check_while, check_loop, SpecError
from .util import proper_plural, get_lines, loc_in_lines, join_lines, LocationError
from .version import version_str
from optparse import OptionParser
from ply.yacc import YaccError
from time import strftime


verbosity = 0

def msg(text, raw=False, min_verbosity=1):
    global verbosity

    if verbosity >= min_verbosity:
        if not raw:
            print("[%s]  %s" % (strftime("%H:%M:%S"), text))
        else:
            print(text)


class MainError(Exception):
    def __init__(self, msg=None):
        if msg is None:
            super(MainError, self).__init__()
        else:
            super(MainError, self).__init__(msg)


class Main(object):
    def read_file(self, filename):
        msg("Reading %s." % filename)

        try:
            lines = get_lines(filename)
        except IOError as e:
            raise MainError("Failed to read %s:\n%s" % (filename, e))

        if any(line.find("\t") != -1 for line in lines):
            raise MainError("Failed to read %s: file contains tab characters." % filename)

        self._filename = filename
        self._lines = lines


    def _exc_with_loc(self, exc):
        result = []

        if isinstance(exc, LocationError) and len(exc.locations) != 0:
            result.append("")
            for loc in exc.locations:
                if hasattr(self, "_trans"):
                    # Transform exception lexpos to line/column.
                    expand_lexpos(loc, self._trans, self._lines)
                for line in loc_in_lines(loc, self._lines):
                    result.append("  %s" % line)

        # Only call str(exc) now, so that it can use transformed
        # lexpos values from expand_lexpos above (which modifies
        # locations in question in-place).
        return [str(exc)] + result


    def prepare_parser(self):
        msg("Preparing parser.")

        self._parser = Parser()


    def _print_error(self, while_error, loop_error):
        if while_error is not None:
            assert isinstance(while_error, Exception)
            print("[-] <WHILE>  %s is not a while program because of the following:" % self._filename)
            print(join_lines(self._exc_with_loc(while_error), indent=13))
            # Without while program we cannot continue.
            raise MainError
        elif loop_error is not None:
            assert isinstance(loop_error, Exception)
            print("[+] <WHILE>  %s is a while program." % self._filename)
            print("\n[-] <LOOP>   %s is not a loop program because of the following:" % self._filename)
            print(join_lines(self._exc_with_loc(loop_error), indent=13))
        else:
            print("[+] <LOOP>   %s is a loop program (and thus while program)." % self._filename)


    def parse_file_input(self):
        msg("Parsing input.")

        try:
            (data, self._trans) = prepare(self._lines)
            self.program = self._parser(data)
        except ParseError as e:
            # This will raise a MainError.
            self._print_error(e, None)
        except YaccError as e:
            raise MainError("Failed to parse %s because of an internal parser error:\n%s" %
                            (self._filename, e))
        except UnicodeError as e:
            raise MainError("Failed to parse %s because of a string encoding error. Most likely, "
                            "you are not using Python 3.0 or later." % self._filename)


    def check_specification(self):
        msg("Checking specification.")

        def try_check(check):
            try:
                check(self.program)
            except SpecError as e:
                # Checks failed.
                return e
            else:
                # Everything OK.
                return ()

        # In the following, None means "unknown", while an exception
        # or () means "error" and "check succeeded", respectively.
        fail_common = try_check(check_common)
        fail_while  = try_check(check_while ) if fail_common == () else None
        fail_loop   = try_check(check_loop  ) if fail_while  == () else None

        if fail_loop == ():
            # Common, while, and loop checks successful.
            errors = (None, None)
        elif fail_while == ():
            # While test succeeded but loop test failed.
            errors = (None, fail_loop)
        else:
            # Common or while failed, no loop test done.
            errors = (fail_while if fail_common == () else fail_common, None)

        # This raises a MainError in case we cannot continue (ie. when
        # common checks or while checks failed).
        self._print_error(*errors)


    def _format_result(self, exec_env, result=None):
        return ("%s(%s) = %s"
                % ( exec_env["main_name_"]
                  , ", ".join(str(arg) for arg in exec_env["arguments_"])
                  , ("%d" % exec_env["ret_value_"]) if result is None else result
                  ))


    def compile_program(self, show_print):
        msg("Compiling program.")

        exec_str = \
            "%s\n" \
            "# globals_ refers to the builtin globals().\n" \
            "# main_name_ is the name of the last function.\n" \
            "# arguments_ is the list of integer arguments.\n" \
            "# ret_value_ is used to return the final result.\n" \
            "ret_value_ = globals_()[main_name_](*arguments_)\n" \
            % self.program.code()

        msg("########################################################################", raw=True, min_verbosity=2)
        msg(exec_str                                                                  , raw=True, min_verbosity=2)
        msg("########################################################################", raw=True, min_verbosity=2)

        import sys
        if sys.version_info[0] >= 3:
            # Code suitable for Python 3.x.
            from .exec_p3 import exec_program
        else:
            # Code suitable for Python 2.x.
            from .exec_p2 import exec_program

        main_fun = self.program.defs[-1]

        def execute(arguments):
            if len(arguments) != main_fun.arity():
                raise MainError("\nUnable to call function `%s': got %s, expected %s."
                                % ( main_fun.name()
                                  , proper_plural(len(arguments), "argument")
                                  , proper_plural(main_fun.arity(), "argument")
                                  ))

            # By appending an underscore to the following global variables we
            # make sure that they cannot be accessed from within the program:
            # underscore is not a valid character in while or loop programs.
            exec_env = { "globals_"   : globals
                       , "main_name_" : main_fun.name()
                       , "arguments_" : arguments
                       , "ret_value_" : None
                       }

            frame_start = "---[ start of print output ]--------------------------------------------"
            frame_end   = "---[ end of print output ]----------------------------------------------"

            def print_start():
                if show_print:
                    print("\n%s" % frame_start)

            def print_end():
                if show_print:
                    print(frame_end)

            try:
                print_start()
                exec_program(exec_str, exec_env, show_print=show_print)
                print_end()
            except Exception as e:
                print_end()
                print("\nFailed to evalute the function defined by %s." % self._filename)
                print("\nIn case of a while program, this might mean that the function is not defined for the given argument tuple." \
                      "\nIn case of a loop program, this might mean that this syntax checker is malfunctioning. Please report this.")
                print("\nHere are some details:\n<%s> %s" % (type(e).__name__, e))
                print("\nThe result might be:\n  %s" % self._format_result(exec_env, "not defined"))
                raise MainError

            return exec_env

        return execute


    def run_program(self, arguments):
        run = self.compile_program(show_print=True)

        msg("Running program.")

        env = run(arguments)
        print("\nThe result is:\n  %s" % self._format_result(env))


    def test_program(self, test_lines, test_filename, show_print):
        run = self.compile_program(show_print=show_print)

        msg("Testing program.")

        print("\nThe test results are:")

        passed = 0
        failed = 0
        pass_str = "[OK]"
        fail_str = "[  ]"

        for line in test_lines:
            values = []
            for value in line.split():
                try:
                    values.append(int(value))
                except ValueError:
                    raise MainError("%s contains invalid integer value `%s'." % (test_filename, value))

            if len(values) < 1:
                # Empty line.
                continue

            env = run(values[:-1])

            if show_print or passed + failed == 0:
                print("")

            if env["ret_value_"] == values[-1]:
                print("  %s  %s" % (pass_str, self._format_result(env)))
                passed += 1
            else:
                print("  %s  %s, but expected %d" % (fail_str, self._format_result(env), values[-1]))
                failed += 1

        print("\n  Out of %s, %s %d passed and %s %d failed."
              % (proper_plural(passed + failed, "test"), pass_str, passed, fail_str, failed))


def main():
    global verbosity, version

    opt_parser = OptionParser(usage="usage: %prog [options] file [arguments]", version="%%prog %s" % version_str())
    opt_parser.add_option("-v", "--verbose", action="count", dest="verbosity",
                          help="increase verbosity", default=0)
    opt_parser.add_option("-e", "--evaluate", action="store_true", dest="evaluate",
                          help="evaluate function defined by file", default=False)
    opt_parser.add_option("-t", "--test", action="store", type="string", dest="test", metavar="FILE",
                          help="test with expected values from FILE", default=None)
    opt_parser.add_option("-T", action="store_true", dest="test_print",
                          help="show print output when running tests", default=False)
    opt_parser.disable_interspersed_args()

    try:
        (options, args) = opt_parser.parse_args()
        verbosity = options.verbosity

        # Process positional arguments.

        if len(args) < 1:
            opt_parser.error("No input file given.")
        filename = args[0]

        arguments = []
        for arg in args[1:]:
            try:
                arguments.append(int(arg))
            except ValueError:
                opt_parser.error("Invalid integer argument `%s'." % arg)

        if not options.evaluate and len(arguments) != 0:
            opt_parser.error("Function argument (%d) without -e." % arguments[0])

        # Check remaining arguments.

        if options.test is not None:
            try:
                test_lines = get_lines(options.test)
            except IOError as e:
                raise MainError("Failed to read %s:\n%s" % (options.test, e))

        # Now do some work.

        main = Main()
        main.read_file(filename)
        main.prepare_parser()
        main.parse_file_input()

        msg("########################################################################", raw=True, min_verbosity=2)
        msg(main.program.code()                                                       , raw=True, min_verbosity=2)
        msg("########################################################################", raw=True, min_verbosity=2)

        main.check_specification()

        if options.evaluate:
            print("\nI will now try and evaluate the function defined by %s." % filename)
            main.run_program(arguments)

        if options.test is not None:
            print("\nI will now try and test %s according to %s." % (filename, options.test))
            main.test_program(test_lines, test_filename=options.test, show_print=options.test_print)

    except MainError as e:
        if len(e.args) != 0:
            print("%s" % e)
