from collections import defaultdict
from functools import reduce


# Convenience "constants" for the Tracker class defined below.
class VARIABLE: pass
class FUNCTION: pass
class STATEMENT: pass

# Utility class that records a set of "tracked" identifiers (or other,
# arbitrary objects), stored in different categories such as variable,
# function, or statement (further categories can be used without prior
# declaration).
class Tracker(object):
    def __init__(self):
        super(Tracker, self).__init__()
        # This is a dict(category: dict(name: list of origins)).
        self._tracked = defaultdict(lambda: defaultdict(lambda: list()))

    def track(self, *args):
        def record(category, name, origin=None):
            self._tracked[category][name].append(origin)

        for arg in args:
            if isinstance(arg, Tracker):
                for category, data in arg._tracked.items():
                    for name in data:
                        record(category, name, arg)
            elif type(arg) is tuple and len(arg) in (2, 3):
                record(*arg)
            else:
                raise TypeError("Argument is neither 2-tuple nor "
                                "3-tuple nor Tracker (%r)." % arg)

    def variables(self):
        return set(self._tracked[VARIABLE].keys())

    def functions(self):
        return set(self._tracked[FUNCTION].keys())

    def statements(self):
        return set(self._tracked[STATEMENT].keys())

    def _lookup(self, category, name, slice_):
        assert name in self._tracked[category]
        origin = self._tracked[category][name]
        assert len(origin) != 0

        result = []
        for org in origin[slice_]:
            if isinstance(org, Tracker):
                result.extend(org._lookup(category, name, slice_))
            elif org is not None:
                result.append(org)
            else:
                result.append(self)

        return result

    def find_first(self, category, name):
        # This only examines the first entry at each level.
        return self._lookup(category, name, slice(0, 1))[0]

    def collect_all(self, category, name):
        # This call collects all the entries at all levels.
        return self._lookup(category, name, slice(0, None))


# Objects of the Location class indicate positions in source code.
# They can be specified either in terms of line and column (1-based),
# or "lexpos" which is the character index in the lexer's data stream
# (0-based).
class Location(object):
    def __init__(self, line=None, column=None, lexpos=None):
        super(Location, self).__init__()
        assert line is None or type(line) is int
        assert column is None or type(column) is int
        assert lexpos is None or type(lexpos) is int
        self.line = line
        self.column = column
        self.lexpos = lexpos

    def __str__(self):
        result = []
        def push(what):
            if getattr(self, what) is not None:
                result.append("%s %d" % (what, getattr(self, what)))
        push("line")
        push("column")
        push("lexpos")
        if len(result) != 0:
            return ", ".join(result)
        else:
            return "<unknown>"


# This defines a class of "located" exceptions, i.e., errors that
# happen during parsing or checking and which might have several
# source locations associated. The locations are automatically
# included in the textual representation of the exception.
class LocationError(Exception):
    def __init__(self, msg, *locs):
        super(LocationError, self).__init__(msg)
        assert all(isinstance(loc, Location) for loc in locs)
        self.locations = locs

    def __str__(self):
        msg = super(LocationError, self).__str__()
        if len(self.locations) == 0:
            return msg
        else:
            return "%s %s" % (msg, " and ".join("(%s)" % loc for loc in self.locations))

    def add_location(self, loc):
        assert isinstance(loc, Location)
        self.locations = tuple(list(self.locations) + [loc])

class ParseError(LocationError):
    pass

class SpecError(LocationError):
    pass


# Convenience function that indents the given code by two spaces as
# used in the string representation given for statement blocks, and
# function definitions.
def indent(txt):
    return "".join( ["  %s\n" % line for line in str(txt).split("\n")[:-1]] )


# Convenience function that joins a list of lines (str), optionally
# indenting each line by the given number of spaces.
def join_lines(lines, indent=0):
    return "\n".join( ["%s%s" % (" " * indent, line) for line in lines] )


# Convenience function that gives the proper singular or plural noun
# depending on whether some quantity is equal to 1 or not.
def proper_plural(count, singular, plural=None, word_only=False):
    if plural is None:
        plural = "%ss" % singular

    word = plural if count != 1 else singular

    if word_only:
        return word
    else:
        return "%d %s" % (count, word)


# Convenience function that returns an overview of the source at the
# given location, marking it in the text; the return value is a list
# of lines.
def loc_in_lines(location, lines):
    (lineno, offset) = (location.line, location.column)

    # To make calculations a bit easier, we switch column to 0-based
    # "offset" and use -1 for None values (both lineno and offset).
    if lineno is None:
        lineno = -1

    if offset is None:
        offset = -1
    else:
        offset -= 1

    # Check for valid line and column. Column can be -1 (unknown) or
    # otherwise be between 0 (first character) and line length (just
    # past the last character).
    if 1 <= lineno <= len(lines) and -1 <= offset <= len(lines[lineno-1]):
        line = lines[lineno-1]
    elif lineno == len(lines) + 1 and offset == -1:
        # This is the special marker for just past the last line in
        # the document: pretend it is an empty line and show it.
        line = ""
        offset = 0
    else:
        # Somehow this is not a valid source location.
        line = "<line not available>"
        offset = 0

    if offset == -1:
        # Use first non-space character.
        offset = len(line) - len(line.lstrip(" "))

    intro = "l.%d:  " % lineno
    return [ "%s%s"  % (intro, line)
           , "%s%s^" % (" " * len(intro), " " * offset)
           ]


# Convenience function that returns an array of lines read from the
# given file. Lines returned from this function do not contain any
# trailing newline characters.
def get_lines(filename):
    import sys

    if sys.version_info[0] >= 3:
        # In Python 3.x, "open" has to decode the file it reads since
        # "str" is the generic (and only) string type. Since we don't
        # want any exceptions (UnicodeDecodeError etc.) to be raised
        # here, we tell "open" to replace any malformed substrings
        # (which typically are just comments anyway) by "?".
        kwds = {"errors": "replace"}
    else:
        # In Python 2.x, "open" simply returns the binary data it has
        # read non-decoded, so that's not an issue here (also, "open"
        # doesn't have any keyword arguments in this Python version).
        kwds = {}

    with open(filename, **kwds) as f:
        return [line.rstrip("\r\n") for line in f]
