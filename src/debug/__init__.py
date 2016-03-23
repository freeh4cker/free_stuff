##########################################################################
# Copyright (c) 2015 Bertrand Néron. All rights reserved.                #
# Use of this source code is governed by a BSD-style license that can be #
# found in the LICENSE file.                                             #
##########################################################################

__author__ = 'bertrand Néron'

from functools import wraps
import sys
import inspect
import linecache


def _trace(prefix, levels, max_depth, output):
    """
    it's a function generator, the returned function can be used as argument to sys.settrace
    to trace code. This function allow to encapsulated data along the function
    provided to sys.settrace

    :param prefix: to prefix any debug output
    :type prefix: string
    :param levels: events to display. The following constants are available:

    * callby: trace which code call the decorated function
    * call: trace call made by this function
    * line: trace each line executed by this function
    * return: trace the values returned by the decorated function

    these flags can be combined like: 'call|return' or 'call|line|return' on so on

    :type levels: set
    :param max_depth: the maximum of nested call to track (-1 to all levels)
    :type max_depth: int
    :param output: where to print the debug statements
    :type output: file object
    :return: a callback to provide to sys.settrace
    :rtype: function
    """
    depth = -1

    def tt(frame, event, arg):
        nonlocal depth
        if event == 'call':
            depth += 1
        elif event == 'return':
            depth -= 1

        if depth < max_depth or max_depth < 0:
            if event in levels:
                nested = '>>' * depth + ' ' if depth else ''
                indent = ' ' * 4 * depth if depth else ''
                filename = frame.f_globals["__file__"]
                lineno = frame.f_lineno
                tpl_begining = "{prefix} {nested}{filename}: {lineno}"
                debug_output_start = tpl_begining.format(
                    prefix=prefix,
                    nested=nested,
                    filename=filename,
                    lineno=lineno,
                )

                if event == 'call':
                    with_args = {}
                    for k, v in frame.f_locals.items():
                        with_args[k] = v.__qualname__ if inspect.isfunction(v) else v
                    with_args = ', '.join(["{}={}".format(k, v) for k, v in with_args.items()])
                    tpl_body = """{indent}{func_name} {with_args}"""
                    with_args = 'called with {}'.format(with_args) if with_args else 'called'
                    debug_output_body = tpl_body.format(
                        indent=indent,
                        func_name=frame.f_code.co_name,
                        with_args=with_args
                    )

                elif event == 'line':
                    if depth < max_depth or max_depth < 0:
                        if event in levels:
                            line = linecache.getline(filename, lineno).rstrip()
                            tpl_body = "{indent}{line}"
                            debug_output_body = tpl_body.format(
                                indent=indent,
                                line=line
                            )

                elif event == 'return':
                    if depth < max_depth or max_depth < 0:
                        if event in levels:
                            line = linecache.getline(filename, lineno)
                            tpl = """{indent}< {r_value} > was returned by {func_name}"""
                            debug_output_body = tpl.format(
                                indent=indent,
                                func_name=frame.f_code.co_name,
                                line=line.rstrip(),
                                r_value=arg
                            )
                print("{:<30}| {}".format(debug_output_start, debug_output_body),
                      file=output)
        return tt
    return tt


def f_trace(prefix='', levels='', max_depth=1, output=sys.stdout):
    """
    A function decorator to help to debug the decorated function, allow to trace
    some events specified by levels.

    :param prefix: to prefix any debug output
    :type prefix: string
    :param levels: events to display. The following constants are available:

    * callby: trace which code call the decorated function
    * call: trace call made by this function
    * line: trace each line executed by this function
    * return: trace the values returned by the decorated function

    these flags can be combined like: 'call|return' or 'call|line|return' on so on

    :type levels: string
    :param max_depth: the maximum of nested call to track (-1 to all levels)
    :type max_depth: int
    :param output: where to print the debug statements
    :type output: file object
    :return: a decorated function
    :rtype: function
    """
    levels = {evt.strip() for evt in levels.split('|')}

    def logger(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(prefix, "START", func.__qualname__, prefix,
                  file=output
                  )
            if 'callby' in levels:
                for frame in inspect.stack()[::-1][:-1]:
                    f_o, filename, lineno, c_name, co_str, *_ = frame
                    print("{prefix} called by {caller_name} {filename}: {lineno} {co_str}".format(
                        prefix=prefix,
                        filename=filename,
                        lineno=lineno,
                        caller_name=c_name,
                        co_str=co_str[0].rstrip(),
                        ),
                        file=output
                    )
                if levels & {'call', 'line', 'return'}:
                    print(prefix, '=' * 10, 'GO INSIDE', func.__qualname__, '=' * 10,
                          file=output
                          )
            sys.settrace(_trace(prefix, levels, max_depth, output))
            _res = func(*args, **kwargs)
            sys.settrace(None)
            print(prefix, 'END', func.__qualname__, prefix, file=output)
            return _res
        return wrapper
    return logger
