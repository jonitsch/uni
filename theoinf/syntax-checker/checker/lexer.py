from .ast import Identifier
from .util import Location, ParseError
import re


class Lexer(object):
    description = {}

    # List of keywords that are not valid identifiers.
    keywords = ( "not", "and", "or", "if", "else", "while", "for", "in", "range", "def", "return"
               , "print", "False", "class", "finally", "is", "None", "continue", "lambda"
               , "try", "True", "from", "nonlocal", "del", "global", "with", "as", "elif"
               , "yield", "assert", "import", "pass", "break", "except", "raise"
               )
    keywords = frozenset(keywords)

    # List of keywords that are actually used in grammar.
    keywords_used = ( "not", "and", "or", "if", "else", "while", "for", "in", "range", "def", "return"
                    , "print"
                    )
    keywords_used = frozenset(keywords_used)

    # List of miscellaneous symbols.
    symbols = { "+" : ("PLUS", "arithmetic operation (+)")
              , "-" : ("MINUS", "arithmetic operation (-)")
              , "<" : ("LT", "relational operator (<)")
              , "<=": ("LE", "relational operator (<=)")
              , ">" : ("GT", "relational operator (>)")
              , ">=": ("GE", "relational operator (>=)")
              , "==": ("EQ", "relational operator (==)")
              , "!=": ("NE", "relational operator (!=)")
              , "(" : ("LPAREN", "opening parenthesis '('")
              , ")" : ("RPAREN", "closing parenthesis ')'")
              , "[" : ("LBRACKET", "opening bracket '['")
              , "]" : ("RBRACKET", "closing bracket ']'")
              , "," : ("COMMA", "comma ','")
              , ":" : ("COLON", "colon ':'")
              , "=" : ("ASSIGN", "assignment '='")
              }

    # Put these regexes in brackets to distinguish between \b (backspace)
    # and \b (empty string at beginning of word) defined within regexes.
    special = { r"[\n]" : ("NEWLINE", "end of line")
              , r"[\t]" : ("INDENT", "indented block")
              , r"[\b]" : ("DEDENT", "dedented block")
              }

    # Tell PLY to skip whitespace.
    t_ignore = " "

    # This is used by PLY, as are all class attrs that start with "t_".
    tokens = tuple(kw.upper() for kw in keywords_used) + \
             tuple(tok for tok, desc in symbols.values()) + \
             tuple(tok for tok, desc in special.values()) + \
             ( "NUMBER", "IDENTIFIER", "KEYWORD"
             )

    for sym, (tok, desc) in symbols.items():
        # Setup regex tokens for symbols.
        locals()["t_%s" % tok] = re.escape(sym)

    for sym, (tok, desc) in special.items():
        # Setup tokens for special items.
        locals()["t_%s" % tok] = sym

    # Provide a textual description for every token.
    description.update((kw.upper(), "keyword `%s'" % kw) for kw in keywords)
    description.update((tok, desc) for sym, (tok, desc) in symbols.items())
    description.update((tok, desc) for sym, (tok, desc) in special.items())
    description.update(( ("NUMBER", "number")
                       , ("IDENTIFIER", "identifier")
                       , ("KEYWORD", "Python keyword")
                       ))

    def t_IDENTIFIER(self, t):
        r"[a-zA-Z][a-zA-Z0-9]*"
        if t.value in self.keywords_used:
            t.type = t.value.upper()
        elif t.value in self.keywords:
            t.type = "KEYWORD"
        else:
            t.value = Identifier(t)
        return t

    def t_NUMBER(self, t):
        r"(0|[1-9][0-9]*)"
        t.value = int(t.value)
        return t

    def t_COMMENT(self, t):
        r"[#][^\n]*"
        pass

    def t_error(self, t):
        raise ParseError("Unexpected character (%r)." %
                         t.value[0], Location(lexpos=t.lexpos))

    def __init__(self):
        super(Lexer, self).__init__()

        # Create PLY lexer.
        from ply.lex import lex, NullLogger
        self.lexer = lex(module=self, debug=False,
                         errorlog=NullLogger())


def prepare(lines):
    (INDENT, DEDENT, NEWLINE) = ("\t", "\b", "\n")

    trans = []
    def update(column=()):
        # Update translation dictionary, allowing for conversion
        # between lexpos and line/column (both are 1-based).
        if column == ():
            trans.append((lexpos, lineno, depth[-1] + 1))
        else:
            trans.append((lexpos, lineno, column))

    lineno = 0
    lexpos = 0
    depth = [0]

    result = []
    for line in lines:
        lineno += 1
        line = line.rstrip("\r\n")

        # Complain about any control characters. We don't want any
        # tabs in particular (they mess up the indention and error
        # reporting output).
        match = re.search(r"[\x00-\x19\x7f]", line)
        if match is not None:
            raise ParseError("Illegal character (%r) found." % match.group(0),
                             Location(line=lineno, column=(match.start(0)+1)))

        # Split line into leading whitespace (indention), the line
        # proper, and any trailing comments (regular expression is
        # constructed in a way that the match always succeeds).
        match = re.match(r"^([ ]*)([^#]*)(#.*)?$", line)
        assert match is not None
        white = len(match.group(1))
        text = match.group(2)

        # If there is no text (the entire line is whitespace which
        # is possibly followed by a comment), don't output it.
        if len(text) == 0:
            continue

        # Perform indention calculation, inserting both INDENT and
        # DEDENT characters (or tokens) as necessary. Updating the
        # translation dictionary without column data before moving
        # lexpos ensures that for errors pointing to INDENT/DEDENT
        # only the line data is reported (ie. no column info).
        if white > depth[-1]:
            # More indented than previous line.
            update(column=None)
            result.append(INDENT)
            lexpos += 1
            depth.append(white)
        elif white < depth[-1]:
            # Less indented than previous line.
            while len(depth) != 0 and white < depth[-1]:
                update(column=None)
                result.append(DEDENT)
                lexpos += 1
                depth.pop()
            if len(depth) == 0 or white != depth[-1]:
                raise ParseError("Dedention does not match any outer "
                                 "indention level.", Location(line=lineno))

        # Record current position in translation dict.
        update()

        # Finally, append to result and update lexpos.
        result.append(text)
        lexpos += len(text)

        # Record explicit EOL (better match comments).
        update(column=(white+len(text.rstrip(" "))+1))
        result.append(NEWLINE)
        lexpos += 1

    # The following adds only dedents at the end of the document. The
    # "end of the document" is the virtual line "len(lines) + 1" with
    # no column set, so update lineno accordingly.
    lineno += 1

    # As promised above, add dedents now for all remaining indents.
    while len(depth) > 1:
        update(column=None)
        result.append(DEDENT)
        lexpos += 1
        depth.pop()

    return ("".join(result), trans)


# This transforms the lexpos in the given location back to the
# original line and column in the source file. It does so by
# inspecting the translation dict returned by prepare().
def expand_lexpos(loc, trans, lines):
    if loc.lexpos is not None and (loc.line is None and loc.column is None):
        if loc.lexpos == -1:
            # End of input.
            loc.line = len(lines)
            if len(lines) != 0:
                loc.column = len(lines[-1].rstrip("\n\r")) + 1
        else:
            for lexpos, line, column in reversed(trans):
                if loc.lexpos >= lexpos:
                    loc.line = line
                    if column is not None:
                        loc.column = column + (loc.lexpos - lexpos)
                    break
    loc.lexpos = None
