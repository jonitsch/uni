from .ast import *
from .lexer import Lexer
from .util import ParseError
import re


class UnexpectedTokenError(Exception):
    def __init__(self, token):
        super(UnexpectedTokenError, self).__init__(token)
        self.token = token


class Parser(object):
    tokens = Lexer.tokens

    # Defining some non-terminal aliases: these are expected to match
    # and will report a corresponding error through additional rules,
    # defined at the end of this parser.
    def p_identifier(self, p):
        "identifier : IDENTIFIER"
        p[0] = p[1]
    def p_assign(self, p):
        "assign : ASSIGN"
        p[0] = p[1]
    def p_comma(self, p):
        "comma : COMMA"
        p[0] = p[1]
    def p_colon(self, p):
        "colon : COLON"
        p[0] = p[1]
    def p_lparen(self, p):
        "lparen : LPAREN"
        p[0] = p[1]
    def p_lbracket(self, p):
        "lbracket : LBRACKET"
        p[0] = p[1]
    def p_rparen(self, p):
        "rparen : RPAREN"
        p[0] = p[1]
    def p_rbracket(self, p):
        "rbracket : RBRACKET"
        p[0] = p[1]
    def p_newline(self, p):
        "newline : NEWLINE"
        p[0] = p[1]
    def p_indent(self, p):
        "indent : INDENT"
        p[0] = p[1]
    def p_dedent(self, p):
        "dedent : DEDENT"
        p[0] = p[1]
    def p_in(self, p):
        "in : IN"
        p[0] = p[1]
    def p_range(self, p):
        "range : RANGE"
        p[0] = p[1]

    # Defining non-terminal: arithop.
    def p_arithop(self, p):
        """
        arithop : PLUS
                | MINUS
        """
        p[0] = p[1]
    # Defining non-terminal: logicop.
    def p_logicop(self, p):
        """
        logicop : AND
                | OR
        """
        p[0] = p[1]
    # Defining non-terminal: compop.
    def p_compop(self, p):
        """
        compop : LT
               | LE
               | GT
               | GE
               | EQ
               | NE
        """
        p[0] = p[1]

    # Defining non-terminal: expression.
    def p_expression_constant_positive(self, p):
        "expression : NUMBER"
        p[0] = Constant(p, p[1], raw=True)
    def p_expression_constant_negative(self, p):
        "expression : MINUS NUMBER"
        p[0] = Constant(p, -p[2], raw=True)
    def p_expression_variable(self, p):
        "expression : IDENTIFIER"
        p[0] = Variable(p, 1)
    def p_expression_arithop(self, p):
        "expression : LPAREN expression arithop expression rparen"
        p[0] = ArithOp(p, 2, 3, 4)
    def p_expression_funcall(self, p):
        "expression : IDENTIFIER LPAREN expressionlist rparen"
        p[0] = FunCall(p, 1, 3)

    # Defining non-terminal: expressionlist[1].
    def p_expressionlist_proper(self, p):
        "expressionlist : expressionlist1"
        p[0] = p[1]
    def p_expressionlist_empty(self, p):
        "expressionlist : "
        p[0] = []
    def p_expressionlist1_head(self, p):
        "expressionlist1 : expression"
        p[0] = [p[1]]
    def p_expressionlist1_tail(self, p):
        "expressionlist1 : expressionlist1 COMMA expression"
        p[1].append(p[3])
        p[0] = p[1]

    # Defining non-terminal: condition.
    def p_condition_comparison(self, p):
        "condition : LPAREN expression compop expression rparen"
        p[0] = Comparison(p, 2, 3, 4)
    def p_condition_negation(self, p):
        "condition : LPAREN NOT condition rparen"
        p[0] = Negation(p, 3)
    def p_condition_logicop(self, p):
        "condition : LPAREN condition logicop condition rparen"
        p[0] = LogicOp(p, 2, 3, 4)

    # Defining non-terminal: suite.
    def p_suite(self, p):
        "suite : newline indent statementlist1 dedent"
        p[0] = StmtBlock(p, 3)

    # Defining non-terminal: statementlist[1].
    def p_statementlist1_head(self, p):
        "statementlist1 : statement"
        p[0] = [p[1]]
    def p_statementlist1_tail(self, p):
        "statementlist1 : statementlist1 statement"
        p[1].append(p[2])
        p[0] = p[1]

    # Defining non-terminal: statement.
    def p_statement_assign(self, p):
        "statement : IDENTIFIER assign expression newline"
        p[0] = Assignment(p, 1, 3)
    def p_statement_ifthen(self, p):
        "statement : IF condition colon suite"
        p[0] = IfStmt(p, 2, 4)
    def p_statement_ifthenelse(self, p):
        "statement : IF condition colon suite ELSE colon suite"
        p[0] = IfStmt(p, 2, 4, 7)
    def p_statement_while(self, p):
        "statement : WHILE condition colon suite"
        p[0] = WhileStmt(p, 2, 4)
    def p_statement_for(self, p):
        "statement : FOR identifier in range lparen expression comma expression rparen colon suite"
        p[0] = ForStmt(p, 2, 6, 8, 11)
    def p_statement_print(self, p):
        "statement : PRINT lparen expressionlist rparen newline"
        p[0] = PrintStmt(p, 3)

    # Defining non-terminal: identifierlist[1].
    def p_identifierlist_proper(self, p):
        "identifierlist : identifierlist1"
        p[0] = p[1]
    def p_identifierlist_empty(self, p):
        "identifierlist : "
        p[0] = []
    def p_identifierlist1_head(self, p):
        "identifierlist1 : identifier"
        p[0] = [p[1]]
    def p_identifierlist1_tail(self, p):
        "identifierlist1 : identifierlist1 COMMA identifier"
        p[1].append(p[3])
        p[0] = p[1]

    # Defining non-terminal: initline.
    def p_initline_proper(self, p):
        "initline : LBRACKET identifierlist rbracket assign lbracket expressionlist rbracket newline"
        p[0] = InitLine(p, 2, 6)
    def p_initline_empty(self, p):
        "initline : "
        p[0] = None

    # Defining non-terminal: funbody.
    def p_funbody_proper(self, p):
        "funbody : statementlist1"
        p[0] = StmtBlock(p, 1)
    def p_funbody_empty(self, p):
        "funbody : "
        p[0] = None

    # Defining non-terminal: return.
    def p_return(self, p):
        "return : RETURN expression newline"
        p[0] = p[2]

    # Defining non-terminal: fundef.
    def p_fundef(self, p):
        "fundef : DEF identifier lparen identifierlist rparen colon newline indent initline funbody return dedent"
        p[0] = FunDef(p, 2, 4, 9, 10, 11)

    # Defining non-terminal: funlist[1].
    def p_funlist_proper(self, p):
        "funlist : funlist1"
        p[0] = p[1]
    def p_funlist_empty(self, p):
        "funlist : "
        p[0] = []
    def p_funlist1_head(self, p):
        "funlist1 : fundef"
        p[0] = [p[1]]
    def p_funlist1_tail(self, p):
        "funlist1 : funlist1 fundef"
        p[1].append(p[2])
        p[0] = p[1]

    # Defining non-terminal: program.
    def p_program(self, p):
        "program : funlist"
        p[0] = Program(p, 1)

    # The following rules improve error reporting. PLY uses their relative
    # order to resolve grammar ambiguities in one way or another, so don't
    # change that.
    def expected(self, p, idx, expected=None, token=None):
        if expected is None and token is not None:
            expected = Lexer.description[token]
        assert expected is not None
        class Expected(Node):
            def __init__(self):
                super(Expected, self).__init__()
                raise ParseError("Match failed: expecting %s."
                                 % expected, Location(lexpos=p.lexpos(idx)))
        return Expected(p)
    def p_initline_error(self, p):
        "initline : error"
        p[0] = self.expected(p, 1, "initialization line")
    def p_funbody_error(self, p):
        "funbody : error"
        p[0] = self.expected(p, 1, "function body")
    def p_return_error(self, p):
        "return : error"
        p[0] = self.expected(p, 1, "return statement")
    def p_statement_error(self, p):
        "statement : error"
        p[0] = self.expected(p, 1, "statement")
    def p_arithop_error(self, p):
        "arithop : error"
        p[0] = self.expected(p, 1, "arithmetic operation (+, -)")
    def p_logicop_error(self, p):
        "logicop : error"
        p[0] = self.expected(p, 1, "logical operator (and, or)")
    def p_compop_error(self, p):
        "compop : error"
        p[0] = self.expected(p, 1, "relational operator (<, <=, >, >=, ==, !=)")
    def p_expression_error(self, p):
        "expression : error"
        p[0] = self.expected(p, 1, "expression")
    def p_condition_error(self, p):
        "condition : error"
        p[0] = self.expected(p, 1, "condition")
    def p_fundef_error(self, p):
        "fundef : error"
        p[0] = self.expected(p, 1, "function definition")
    def p_identifier_error(self, p):
        "identifier : error"
        p[0] = self.expected(p, 1, token="IDENTIFIER")
    def p_assign_error(self, p):
        "assign : error"
        p[0] = self.expected(p, 1, token="ASSIGN")
    def p_comma_error(self, p):
        "comma : error"
        p[0] = self.expected(p, 1, token="COMMA")
    def p_colon_error(self, p):
        "colon : error"
        p[0] = self.expected(p, 1, token="COLON")
    def p_lparen_error(self, p):
        "lparen : error"
        p[0] = self.expected(p, 1, token="LPAREN")
    def p_lbracket_error(self, p):
        "lbracket : error"
        p[0] = self.expected(p, 1, token="LBRACKET")
    def p_rparen_error(self, p):
        "rparen : error"
        p[0] = self.expected(p, 1, token="RPAREN")
    def p_rbracket_error(self, p):
        "rbracket : error"
        p[0] = self.expected(p, 1, token="RBRACKET")
    def p_newline_error(self, p):
        "newline : error"
        p[0] = self.expected(p, 1, token="NEWLINE")
    def p_indent_error(self, p):
        "indent : error"
        p[0] = self.expected(p, 1, token="INDENT")
    def p_dedent_error(self, p):
        "dedent : error"
        p[0] = self.expected(p, 1, token="DEDENT")
    def p_in_error(self, p):
        "in : error"
        p[0] = self.expected(p, 1, token="IN")
    def p_range_error(self, p):
        "range : error"
        p[0] = self.expected(p, 1, token="RANGE")

    def p_error(self, t):
        # None means EOF.
        self._failed = t

        if t is not None and t.type in ("INDENT", "DEDENT", "KEYWORD"):
            # Not much sense in backtracking: report token now.
            raise UnexpectedTokenError(t)

    def __init__(self):
        super(Parser, self).__init__()

        self._lexer = Lexer()

        from ply.yacc import yacc, NullLogger
        self._parser = yacc(module=self, start="program",
                            write_tables=False, debug=False,
                            errorlog=NullLogger())

    def __call__(self, data):
        self._failed = ()

        try:
            # Need tracking for position recording.
            result = self._parser.parse(data, lexer=self._lexer.lexer,
                                        tracking=True, debug=False)
        except UnexpectedTokenError as e:
            # Handle unexpected token in block below.
            self._failed = e.token

        if self._failed != ():
            # p_error must have been called, but none of the other
            # error reporting matchers: fail the unexpected token.
            if self._failed is None:
                what = "end of input"
                where = -1
            else:
                what = Lexer.description[self._failed.type]
                where = self._failed.lexpos

            raise ParseError("Match failed: unexpected %s."
                             % what, Location(lexpos=where))

        return result
