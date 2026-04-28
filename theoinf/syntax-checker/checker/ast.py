from .util import Tracker, VARIABLE, FUNCTION, STATEMENT, ParseError, Location, indent
from ply.lex import LexToken
from ply.yacc import YaccProduction


# This metaclass provides all classes that implement it (which will be
# the children of class Node defined below) with location tracking. It
# also makes constructing syntax tree nodes from within PLY's parsing
# routines easier by modifying the constructor call so that it takes
# the location data directly from PLY's parse node. Also exceptions
# raised in the constructor (that don't have an explicit location
# attribute) will get modified so they show the current parser
# location.
class Wrapped(type):
    def __init__(cls, name, bases, dict_):
        super(Wrapped, cls).__init__(name, bases, dict_)

        def create(*args, **kwds):
            return cls._create(args, kwds)

        # This adds the static method create to all classes using this
        # metaclass which can be used to call the original __init__.
        setattr(cls, "create", staticmethod(create))

    # This function will be called whenever a new object of the class
    # using this metaclass is to be instantiated by using the simple
    # form ClassName(...). This is redefined here in terms of PLY's
    # parser objects.
    def __call__(cls, pt, *args, **kwds):
        if "raw" in kwds:
            # "raw" is our own keyword argument, so take it. This is a
            # workaround for Python 2.x, where the correct syntax "def
            # __call__(cls, pt, *args, raw=False, **kwds)" is not yet
            # defined.
            raw = kwds["raw"]
            del kwds["raw"]
        else:
            raw = False

        if isinstance(pt, YaccProduction):
            if not raw:
                assert all(type(i) is int for i in args)
                return cls._create(tuple(pt[i] for i in args),
                                   kwds, lexpos=pt.lexpos(0))
            else:
                return cls._create(args, kwds, lexpos=pt.lexpos(0))
        elif isinstance(pt, LexToken):
            if not raw:
                assert len(args) == 0
                return cls._create((pt.value,), kwds, lexpos=pt.lexpos)
            else:
                return cls._create(args, kwds, lexpos=pt.lexpos)
        else:
            raise TypeError("Don't know how to handle %s." % type(pt))

    def _create(cls, args, kwds, lexpos=None):
        assert type(args) is tuple
        assert type(kwds) is dict

        inst = cls.__new__(cls, *args, **kwds)
        assert type(inst) is cls

        if lexpos is None:
            inst.location = None
        else:
            inst.location = Location(lexpos=lexpos)

        try:
            inst.__init__(*args, **kwds)
        except ParseError as e:
            if len(e.locations) == 0 and inst.location is not None:
                e.add_location(inst.location)
            raise

        return inst


import sys
if sys.version_info[0] >= 3:
    # Code suitable for Python 3.x.
    from .node_p3 import Node
else:
    # Code suitable for Python 2.x.
    from .node_p2 import Node


class Identifier(Node):
    def __init__(self, name):
        super(Identifier, self).__init__()
        assert type(name) is str
        self.name = name


class Expression(Node, Tracker):
    pass

class Constant(Expression):
    def __init__(self, value):
        super(Constant, self).__init__()
        assert type(value) is int
        self._value = value

    def code(self):
        return "%d" % self._value

    def value(self):
        return self._value

class Variable(Expression):
    def __init__(self, ident):
        super(Variable, self).__init__()
        assert isinstance(ident, Identifier)
        self.track((VARIABLE, ident.name, ident))
        self.name = ident.name

    def code(self):
        return "%s" % self.name

class ArithOp(Expression):
    def __init__(self, expr_a, op, expr_b):
        super(ArithOp, self).__init__()
        assert isinstance(expr_a, Expression)
        assert type(op) is str
        assert isinstance(expr_b, Expression)
        self.track(expr_a, expr_b)
        self.expr_a = expr_a
        self.op = op
        self.expr_b = expr_b

    def code(self):
        return "(%s %s %s)" % (self.expr_a.code(), self.op, self.expr_b.code())

class FunCall(Expression):
    def __init__(self, ident, args):
        super(FunCall, self).__init__()
        assert isinstance(ident, Identifier)
        assert type(args) is list
        assert all(isinstance(arg, Expression) for arg in args)
        self.track((FUNCTION, ident.name), *args)
        self.name = ident.name
        self.args = args

    def code(self):
        return "%s(%s)" % (self.name, ", ".join(arg.code() for arg in self.args))

    def arity(self):
        return len(self.args)


class Condition(Node, Tracker):
    pass

class Comparison(Condition):
    def __init__(self, expr_a, op, expr_b):
        super(Comparison, self).__init__()
        assert isinstance(expr_a, Expression)
        assert type(op) is str
        assert isinstance(expr_b, Expression)
        self.track(expr_a, expr_b)
        self.expr_a = expr_a
        self.op = op
        self.expr_b = expr_b

    def code(self):
        return "(%s %s %s)" % (self.expr_a.code(), self.op, self.expr_b.code())

class Negation(Condition):
    def __init__(self, cond):
        super(Negation, self).__init__()
        assert isinstance(cond, Condition)
        self.track(cond)
        self.cond = cond

    def code(self):
        return "(not %s)" % self.cond.code()

class LogicOp(Condition):
    def __init__(self, cond_a, op, cond_b):
        super(LogicOp, self).__init__()
        assert isinstance(cond_a, Condition)
        assert type(op) is str
        assert isinstance(cond_b, Condition)
        self.track(cond_a, cond_b)
        self.cond_a = cond_a
        self.op = op
        self.cond_b = cond_b

    def code(self):
        return "(%s %s %s)" % (self.cond_a.code(), self.op, self.cond_b.code())


class Statement(Node, Tracker):
    pass

class StmtBlock(Statement):
    def __init__(self, stmts):
        super(StmtBlock, self).__init__()
        assert type(stmts) is list
        assert all(isinstance(stmt, Statement) for stmt in stmts)
        self.track(*stmts)
        self.stmts = stmts

    def code(self):
        return "".join(stmt.code() for stmt in self.stmts)

class Assignment(Statement):
    def __init__(self, target, expr):
        super(Assignment, self).__init__()
        assert isinstance(target, Identifier)
        assert isinstance(expr, Expression)
        self.track((STATEMENT, Assignment), (VARIABLE, target.name, target), expr)
        self.target = target.name
        self.expr = expr

    def code(self):
        return "%s = %s\n" % (self.target, self.expr.code())

class IfStmt(Statement):
    def __init__(self, cond, then_, else_=None):
        super(IfStmt, self).__init__()
        assert isinstance(cond, Condition)
        assert isinstance(then_, Statement)
        assert else_ is None or isinstance(else_, Statement)
        self.track((STATEMENT, IfStmt), cond, then_)
        if else_ is not None:
            self.track(else_)
        self.cond = cond
        self.then_ = then_
        self.else_ = else_

    def code(self):
        if self.else_ is None:
            return "if %s:\n%s" % (self.cond.code(), indent(self.then_.code()))
        else:
            return "if %s:\n%selse:\n%s" % (self.cond.code(), indent(self.then_.code()), indent(self.else_.code()))

class WhileStmt(Statement):
    def __init__(self, cond, body):
        super(WhileStmt, self).__init__()
        assert isinstance(cond, Condition)
        assert isinstance(body, Statement)
        self.track((STATEMENT, WhileStmt), cond, body)
        self.cond = cond
        self.body = body

    def code(self):
        return "while %s:\n%s" % (self.cond.code(), indent(self.body.code()))

class ForStmt(Statement):
    def __init__(self, target, expr_a, expr_b, body):
        super(ForStmt, self).__init__()
        assert isinstance(target, Identifier)
        assert isinstance(expr_a, Expression)
        assert isinstance(expr_b, Expression)
        assert isinstance(body, Statement)
        self.track((STATEMENT, ForStmt), (VARIABLE, target.name, target), expr_a, expr_b, body)
        self.target = target.name
        self.expr_a = expr_a
        self.expr_b = expr_b
        self.body = body

    def code(self):
        return "for %s in range(%s, %s):\n%s" % (self.target, self.expr_a.code(),
                                                 self.expr_b.code(), indent(self.body.code()))

class PrintStmt(Statement):
    def __init__(self, args):
        super(PrintStmt, self).__init__()
        assert type(args) is list
        assert all(isinstance(arg, Expression) for arg in args)
        self.track((STATEMENT, PrintStmt), *args)
        self.args = args

        if len(args) == 0:
            raise ParseError("Empty print statement not allowed.")

    def code(self):
        return "print(%s)\n" % (", ".join(arg.code() for arg in self.args))


class InitLine(Node):
    def __init__(self, vars_, vals_):
        super(InitLine, self).__init__()
        assert type(vars_) is list
        assert all(isinstance(var, Identifier) for var in vars_)
        assert type(vals_) is list
        assert all(isinstance(val, Expression) for val in vals_)
        self._vars = vars_
        has_var = set()
        for var in vars_:
            if var.name in has_var:
                raise ParseError("Duplicate variable `%s' in initialization "
                                 "in function definition." % var.name, var.location)
            has_var.add(var.name)
        for val in vals_:
            if not isinstance(val, Constant) or val.value() != 0:
                raise ParseError("Non-zero or non-constant expression "
                                 "in initialization in function definition.", val.location)
        if len(vars_) != len(vals_):
            raise ParseError("Lengths of variable initialization lists do not match in function definition.")

    def code(self):
        return "[%s] = [%s]\n" % ( ", ".join(var.name for var in self._vars)
                                 , ", ".join(["0"] * len(self._vars))
                                 )

    def variables(self):
        return set(var.name for var in self._vars)

    def var_location(self, name):
        return dict((var.name, var.location) for var in self._vars)[name]

class FunDef(Node, Tracker):
    def __init__(self, name, args, init, body, expr):
        super(FunDef, self).__init__()
        assert isinstance(name, Identifier)
        assert type(args) is list
        assert all(isinstance(arg, Identifier) for arg in args)
        assert isinstance(expr, Expression)
        assert init is None or isinstance(init, InitLine)
        assert body is None or isinstance(body, Statement)
        if body is not None:
            self.track(body)
        self.track(expr)
        self._name = name
        self._args = args
        self._expr = expr
        self._init = init
        self._body = body
        has_arg = set()
        for arg in args:
            if arg.name in has_arg:
                raise ParseError("Duplicate argument `%s' in funtion definition."
                                 % arg.name, arg.location)
            has_arg.add(arg.name)

    def code(self):
        return "def %s(%s):\n%s" \
               % ( self._name.name
                 , ", ".join(arg.name for arg in self._args)
                 , indent("%s%sreturn %s\n" % ( self._init.code() if self._init is not None else ""
                                              , self._body.code() if self._body is not None else ""
                                              , self._expr.code()
                                              ))
                 )

    def name(self):
        return self._name.name

    def arity(self):
        return len(self._args)

    def arguments(self):
        return set(arg.name for arg in self._args)

    def initialized(self):
        return self._init.variables() if self._init is not None else None

    def name_location(self):
        return self._name.location

    def arg_location(self, arg):
        return dict((var.name, var.location) for var in self._args)[arg]

    def ini_location(self, ini):
        return self._init.var_location(ini) if self._init is not None else None

    def init_location(self):
        return self._init.location


class Program(Node):
    def __init__(self, defs):
        super(Program, self).__init__()
        assert type(defs) is list
        assert all(isinstance(fun, FunDef) for fun in defs)
        self.defs = defs

    def code(self):
        return "\n".join("%s" % fun.code() for fun in self.defs)
