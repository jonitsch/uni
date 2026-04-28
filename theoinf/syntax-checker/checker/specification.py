from .ast import Program, FunDef, WhileStmt, FunCall
from .util import proper_plural, SpecError, VARIABLE, FUNCTION, STATEMENT


common_checks = []

# Wrapper to be called as function decorator on "common" checks, i.e.
# checks that apply to both loop and while programs. Using the common
# decorator will register the check to be executed with check_common
# defined below.
def common(check):
    global common_checks
    common_checks.append(check)
    return check


# Checks whether in function definitions with initialization all
# variables used within the function are initialized.
@common
def check_initialization(program):
    for fun in program.defs:
        if fun.initialized() is None:
            # No initialization in this function: nothing to do.
            continue

        used = fun.variables()
        args = fun.arguments()
        init = fun.initialized()

        if len(init & args) != 0:
            var = list(init & args)[0]
            raise SpecError("Name `%s' used both within initialization and as an argument in function `%s'."
                            % (var, fun.name()), fun.arg_location(var), fun.ini_location(var))

        if (used - args) != init:
            init_but_not_used = init - (used - args)
            used_but_not_init = (used - args) - init

            if len(used_but_not_init) != 0:
                var = list(used_but_not_init)[0]
                raise SpecError("Invalid initialization: variable `%s' used but not initialized in function `%s'."
                                % (var, fun.name()), fun.init_location(), fun.find_first(VARIABLE, var).location)
            else:
                assert len(init_but_not_used) != 0
                var = list(init_but_not_used)[0]
                raise SpecError("Invalid initialization: variable `%s' initialized but not used in function `%s'."
                                % (var, fun.name()), fun.ini_location(var))


@common
def check_unique_fun_defs(program):
    defined = dict()

    for fun in program.defs:
        if fun.name() in defined:
            raise SpecError("Duplicate function definition for function `%s'."
                            % fun.name(), defined[fun.name()], fun.name_location())

        defined[fun.name()] = fun.name_location()


@common
def check_fun_and_var_names(program):
    defined = dict((fun.name(), fun.name_location()) for fun in program.defs)

    for fun in program.defs:
        var = fun.variables() | fun.arguments()
        intersect = var & set(defined.keys())

        if len(intersect) != 0:
            var = list(intersect)[0]

            if var in fun.arguments():
                what = "argument"
                where = fun.arg_location(var)
            else:
                what = "variable"
                where = fun.find_first(VARIABLE, var).location

            assert var in defined
            raise SpecError("Use of %s named `%s' prohibited in function `%s': "
                            "there is a function defined with that name."
                            % (what, var, fun.name()), where, defined[var])


@common
def check_fun_calls(program):
    defined = dict((fun.name(), fun) for fun in program.defs)

    for fun in program.defs:
        for name in fun.functions():
            if name not in defined:
                raise SpecError("Function `%s' used but not defined."
                                % name, fun.find_first(FUNCTION, name).location)

            for call in fun.collect_all(FUNCTION, name):
                assert call.name == name

                defined_arity = defined[name].arity()
                if call.arity() != defined_arity:
                    raise SpecError("Function call does not match arity of function `%s': got %s, expected %s."
                                    % ( name
                                      , proper_plural(call.arity(), "argument")
                                      , proper_plural(defined_arity, "argument")
                                      ),
                                    call.location, defined[name].name_location()
                                   )


# Convenience function that includes all common checks for both
# while programs and loop programs.
def check_common(program):
    assert type(program) is Program

    global common_checks
    for what in common_checks:
        what(program)


# Checks whether the given program satisfies the while program
# requirements in addition to the common requirements.
def check_while(program):
    assert type(program) is Program

    if not len(program.defs) >= 1:
        raise SpecError("Program does not contain any function definitions.")


# Checks whether the given program satisfies the loop program
# requirements in addition to the while program requirements
# and the common requirements.
def check_loop(program):
    assert type(program) is Program

    for fun in program.defs:
        if WhileStmt in fun.statements():
            raise SpecError("Invalid use of while loop within function `%s'."
                            % fun.name(), fun.find_first(STATEMENT, WhileStmt).location)

    defined = set()
    for fun in program.defs:
        for call in fun.functions():
            if call not in defined:
                if call == fun.name():
                    raise SpecError( "Calling function `%s' from within its own definition not allowed." % call
                                   , fun.find_first(FUNCTION, call).location
                                   )
                else:
                    def_locs = dict((fun.name(), fun.name_location()) for fun in program.defs)
                    assert call in def_locs
                    raise SpecError( "Calling function `%s' from within function `%s' not allowed." % (call, fun.name())
                                   , fun.find_first(FUNCTION, call).location, def_locs[call]
                                   )

        defined.add(fun.name())

    for fun in program.defs:
        if fun.initialized() is None:
            raise SpecError("Function `%s' lacks initialization of variables."
                            % fun.name(), fun.name_location())
