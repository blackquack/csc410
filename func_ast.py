import sys


class Node(object):
    __slots__ = ()
    """ Abstract base class for AST nodes.
    """
    def children(self):
        """ A sequence of all children that are Nodes
        """
        pass

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and
            children (recursively) to a buffer.

            buf:
                Open IO buffer into which the Node is printed.

            offset:
                Initial offset (amount of leading spaces)

            attrnames:
                True if you want to see the attribute names in
                name=value pairs. False to only see the values.

            nodenames:
                True if you want to see the actual node names
                within their parents.

            showcoord:
                Do you want the coordinates of each Node to be
                displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self,n)) for n in self.attr_names]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            buf.write(' (at %s)' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(
                buf,
                offset=offset + 2,
                attrnames=attrnames,
                nodenames=nodenames,
                showcoord=showcoord,
                _my_node_name=child_name)


class NodeVisitor(object):
    """ A base NodeVisitor class for visiting c_ast nodes.
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these
        methods.

        For example:

        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []

            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the bant nodes
        encountered below the given node. To use it:

        cv = ConstantVisitor()
        cv.visit(node)

        Notes:

        *   generic_visit() will be called for AST nodes for which
            no visit_XXX method was defined.
        *   The children of nodes for which a visit_XXX was
            defined will not be visited - if you need this, call
            generic_visit() on the node.
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """
    def visit(self, node):
        """ Visit a node.
        """
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c_name, c in node.children():
            self.visit(c)


class ArrayRef(Node):
    __slots__ = ('name', 'subscript', 'coord', '__weakref__')
    def __init__(self, name, subscript, coord=None):
        self.name = name
        self.subscript = subscript
        self.coord = coord

    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(("name", self.name))
        if self.subscript is not None: nodelist.append(("subscript", self.subscript))
        return tuple(nodelist)
    
    def __str__(self):
        return "{}[{}]".format(str(self.name), str(self.subscript))

    attr_names = ()


class BinaryOp(Node):
    __slots__ = ('op', 'left', 'right', 'coord', '__weakref__')

    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.left = left
        self.right = right
        self.coord = coord

    def children(self):
        nodelist = []
        if self.left is not None: nodelist.append(("left", self.left))
        if self.right is not None: nodelist.append(("right", self.right))
        return tuple(nodelist)

    def __str__(self):
        return "{} {} {}".format(self.left, self.op, self.right)

    attr_names = ('op', )


class Constant(Node):
    __slots__ = ('value', 'coord', '__weakref__')

    def __init__(self , value, coord=None):
        self.value = value
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __str__(self):
        return str(self.value)

    attr_names = ('type', 'value', )


class ExprList(Node):
    __slots__ = ('exprs', 'coord', '__weakref__')

    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(("exprs[%d]" % i, child))
        return tuple(nodelist)

    def __str__(self):
        return "\n".join(self.exprs)
    
    attr_names = ()


class FuncCall(Node):
    __slots__ = ('name', 'args', 'coord', '__weakref__')

    def __init__(self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord

    def children(self):
        nodelist = []
        if self.name is not None: nodelist.append(("name", self.name))
        if self.args is not None: nodelist.append(("args", self.args))
        return tuple(nodelist)

    def __str__(self):
        return "{}{}".format(self.name, self.args)

    attr_names = ()


class FuncDef(Node):
    __slots__ = ('input_args', 'output_vars', 'body', 'coord', '__weakref__')

    def __init__(self, input_args, output_vars, body, coord=None):
        self.input_args = input_args
        self.output_vars = output_vars
        self.body = body
        self.coord = coord

    def children(self):
        nodelist = []
        if self.body is not None: nodelist.append(("body", self.body))
        if self.input_args is not None: nodelist.append(("args", self.input_args))
        if self.output_vars is not None: nodelist.append(("return", self.output_vars))
        return tuple(nodelist)

    def __str__(self):
        return "fun code_block{} return {} \n {}".format(self.input_args, self.output_vars, self.body)

    attr_names = ()


class ID(Node):
    __slots__ = ('name', 'coord', '__weakref__')

    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    def __str__(self):
        return self.name

    attr_names = ('name', )


class If(Node):
    __slots__ = ('cond', 'iftrue', 'iffalse', 'coord', '__weakref__')
    def __init__(self, cond, iftrue, iffalse, coord=None):
        self.cond = cond
        self.iftrue = iftrue
        self.iffalse = iffalse
        self.coord = coord

    def children(self):
        nodelist = []
        if self.cond is not None: nodelist.append(("cond", self.cond))
        if self.iftrue is not None: nodelist.append(("iftrue", self.iftrue))
        if self.iffalse is not None: nodelist.append(("iffalse", self.iffalse))
        return tuple(nodelist)

    def __str__(self):
        return "if {} then {} else {}".format(self.cond, self.iftrue, self.iffalse)

    attr_names = ()


class ArgsList(Node):
    __slots__ = ('args', 'coord', '__weakref__')

    def __init__(self, args, coord=None):
        self.args = args
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.args or []):
            nodelist.append(("args[%d]" % i, child))
        return tuple(nodelist)

    def __str__(self):
        args = [str(arg) for arg in self.args]
        return "({})".format(', '.join(args))

    attr_names = ()


class Binding(Node):
    __slots__ = ('id', 'expr1', 'expr2', 'coord', '__weakref__')

    def __init__(self, id, expr1, expr2, coord=None):
        self.id = id
        self.expr1 = expr1
        self.expr2 = expr2
        self.coord = coord

    def children(self):
        nodelist = []
        if self.id is not None: nodelist.append(("id", self.id))
        if self.expr1 is not None: nodelist.append(("expr", self.expr1))
        if self.expr2 is not None: nodelist(("expr", self.expr2))
        return tuple(nodelist)
    
    def __str__(self):
        return "let {} = {} in {}".format(self.id, self.expr1, self.expr2)

    attr_names = ()


class RecursiveFunction(Node):
    __slots__ = ('id', 'args', 'expr1', 'expr2', 'coord', '__weakref__')

    def __init__(self, id, args, expr1, expr2, coord=None):
        self.id = id
        self.args = args
        self.expr1 = expr1
        self.expr2 = expr2
        self.coord = coord
  
    def children(self):
        nodelist = []
        if self.id is not None: nodelist.append(("id", self.expr1))
        if self.args is not None: nodelist.append(("args", self.args))
        if self.expr1 is not None: nodelist.append(("expr", self.args))
        if self.expr2 is not None: nodelist(("expr", self.expr2))
        return tuple(nodelist)
  
    def __str__(self):
        return "letrec {} {} = {} in {}".format(self.id, self.args, self.expr1, self.expr2)

    attr_names = ()


class ReturnTuple(Node):
    __slots__ = ('exprs', 'coord')

    def __init__(self, exprs, coord=None):
        self.exprs = exprs

    def children(self):
        nodelist = []
        for i, child in enumerate(self.exprs or []):
            nodelist.append(("exprs[%d]" % i, child))
        return tuple(nodelist)

    def __str__(self):
        return "({})".format(', '.join([str(expr) for expr in self.exprs]))
  
    attr_names = ()
