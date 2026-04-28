# IMPORTANT: When making change be sure to check node_p3.py as well.

from .ast import Wrapped

class Node(object):
    # Through the use of the metaclass Wrapped, each instance of Node
    # has the additional attribute "location". Also all classes that
    # derive from Node have the static method "create" which can be
    # used to call the original __init__.
    __metaclass__ = Wrapped
