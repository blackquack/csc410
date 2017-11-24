from minic.minic_ast import *
import func_ast as func

class AST_C(NodeVisitor):
  def __init__(self, simplify=True):
    self.written_set = set()
    self.read_set = set()
    self.simplify = simplify

    # Keep track of the head binding and tail binding. For example
    # let id = expr1 in expr2, expr2 can be more bindings, so we need to keep
    # reference of the head when we use it for the function. 
    self.head_binding = None
    self.tail_binding = None

  def expr(self, _class, value):
    return {
        Constant: (lambda orig: func.Constant(orig.value)),
        ID: (lambda orig: func.ID(orig.name)),
        ArrayRef: (lambda orig: func.ArrayRef(
          self.expr(orig.name.__class__, orig.name), 
          self.expr(orig.subscript.__class__, orig.subscript))),
        ExprList: (lambda orig: func.ArgsList([self.expr(x.__class__, x) for x in orig.exprs])),
        FuncCall: (lambda orig: func.FuncCall(
          self.expr(orig.name.__class__, orig.name), 
          self.expr(orig.args.__class__, orig.args))),
        BinaryOp: (lambda orig: func.BinaryOp(orig.op, 
          self.expr(orig.left.__class__ , orig.left), 
          self.expr(orig.right.__class__, orig.right)))      
      }.get(_class)(value)
  
  def visit_If(self, condition):
    # Get condition
    cond_expr = self.expr(condition.cond.__class__, condition.cond)

    iftrue_ast = None
    iffalse_ast = None

    if_written_set = set()
    # When the iftrue or iffalse blocks are not None then visit that branch
    # and update the written_set and read_set.
    if not condition.iftrue is None:
      iftrue_ast = AST_C()
      iftrue_ast.visit(condition.iftrue)

      self.written_set.update(iftrue_ast.written_set)
      self.read_set.update(iftrue_ast.read_set)
      if_written_set.update(iftrue_ast.written_set)

    if not condition.iffalse is None:
      iffalse_ast = AST_C()
      iffalse_ast.visit(condition.iffalse)

      self.written_set.update(iffalse_ast.written_set)
      self.read_set.update(iffalse_ast.read_set)
      if_written_set.update(iffalse_ast.written_set)
    
    # Create functional node
    lhs = func.ReturnTuple(if_written_set) if len(if_written_set) > 1 else func.ID(next(iter(if_written_set)))
    
    # Set the expression to be the same as the left hand side assignment if the iftrue or iffalse blocks are None.
    # Otherwise, set the tail binding's second expression to be the left hand side assignment and set the expression
    # as the binding of the associated branch.
    if condition.iftrue is None:
      iftrue_expr = lhs
    else:
      # iftrue_ast.tail_binding.expr2 = lhs
      iftrue_expr = self.simplify_binding(iftrue_ast.head_binding, if_written_set)
    
    if condition.iffalse is None:
      iffalse_expr = lhs
    else:
      # iffalse_ast.tail_binding.expr2 = lhs
      iffalse_expr = self.simplify_binding(iffalse_ast.head_binding, if_written_set)
    
    # Create functional condition node and binding
    if_expr = func.If(cond_expr, iftrue_expr, iffalse_expr)
    self.__create_binding(lhs, if_expr, None)

  def visit_Block(self, block):
    self.generic_visit(block)

  def visit_Assignment(self, assignment):
    self.visit(assignment.rvalue)

    expr1 = self.expr(assignment.rvalue.__class__, assignment.rvalue)

    if isinstance(assignment.lvalue, ID):
      written_var = func.ID(assignment.lvalue.name)
      self.written_set.add(assignment.lvalue.name)
    else:
      written_var = func.ArrayRef(assignment.lvalue.name.name, assignment.lvalue.subscript.name)
      self.written_set.add(assignment.lvalue.name.name)

    self.__create_binding(written_var, expr1, None)

  def visit_BinaryOp(self, binaryop):
    self.generic_visit(binaryop)
    
  def visit_ID(self, id):
    self.read_set.add(id.name)

  def visit_ArrayRef(self, array_ref):
    self.read_set.add(array_ref.name.name)
    self.read_set.add(array_ref.subscript.name)
  
  def __create_binding(self, lhs, expr1, expr2, simplify=True):
    current_binding = func.Binding(lhs, expr1, expr2)
    if self.head_binding is None:
      self.head_binding = current_binding
    if not self.tail_binding is None:
      self.tail_binding.expr2 = current_binding
    self.tail_binding = current_binding

  def simplify_binding(self, binding, return_list):
    head = binding
    prev = None
    curr = binding
    replace = {}
    while isinstance(curr, func.Binding):
      if isinstance(curr.expr1, func.If):
        prev = curr

      if isinstance(curr.id, func.ID):
        # Use FunctionalVistor to replace the variables with constants.
        f_visitor = FunctionalVisitor(curr.expr1, replace)

        # If the expr1 is a let binding, simplify that binding as well.
        # Don't worry about this yet
        # if isinstance(curr.expr1, func.Binding):
        #     curr.expr1 = simplify_binding(curr.expr1)

        # If expr1 is just an expression without any variables, then take out the binding.
        if not f_visitor.var_set:
          replace[curr.id.name] = curr.expr1
          if prev is None:
            if not curr.expr2 is None:
              head = curr.expr2
          else:                
            prev.expr2 = curr.expr2

        # If the variable in expr1 does not appear until the end of the return tuple, then take out the binding.
        elif not curr.id.name in self.read_set:
          f_visitor = FunctionalVisitor(curr.expr1)
          
          # Check if there are any variables in expr1 that are in the written set. If there aren't, then
          # get rid of the binding and set the return tuple variable to the expression.
          if len([var for var in f_visitor.var_set if var in self.written_set]) == 0:
            replace[curr.id.name] = curr.expr1
            if prev is None:
              if not curr.expr2 is None:
                head = curr.expr2
            else:                
              prev.expr2 = curr.expr2
          else:
            prev = curr

        # If expr1 is just a variable and it is is the same as the lhs, then simply take out the binding.
        elif isinstance(curr.expr1, func.ID) and curr.expr1.name == curr.id.name:
          replace[curr.id.name] = curr.expr1
          if prev is None:
            if not curr.expr2 is None:
              head = curr.expr2
          else:
            prev.expr2 = curr.expr2

        # If expr1 is just a constant, then simply take out the binding.
        elif isinstance(curr.expr1, func.Constant):
          replace[curr.id.name] = curr.expr1
          if prev is None:
            if not curr.expr2 is None:
              head = curr.expr2
          else:
            prev.expr2 = curr.expr2
    
        else:
          prev = curr
      

      # Move to the next binding
      curr = curr.expr2

    # Replace each variable in the return tuple if needed
    return_tuple = func.ReturnTuple([replace[var] if var in replace else var for var in return_list])
    if prev is None:
      head = return_tuple
    elif isinstance(head, func.Binding) and head.id == return_tuple:
      head = head.expr1
    else:
      prev.expr2 = return_tuple 
    
    return head

  # Transforms minic block into func_ast starting with FuncDef as parent node
  def transform(self):
    args_list = func.ArgsList(self.read_set.union(self.written_set))
    return_list = list(self.written_set)
    return_tuple = func.ReturnTuple(return_list)
    # For now only worry about let id = ... in ...

    if self.simplify:
      self.head_binding = self.simplify_binding(self.head_binding, return_list)
    else:
      self.tail_binding.expr2 = return_tuple
    
    return func.FuncDef(args_list, return_tuple, self.head_binding)

class FunctionalVisitor(NodeVisitor):
  def __init__(self, node, replace=None):
    self.replace = replace
    self.var_set = set()
    self.visit(node)

  def visit_BinaryOp(self, binaryop):
    if not self.replace is None:
      if isinstance(binaryop.left, func.ID) and binaryop.left.name in self.replace:
        binaryop.left = func.Constant(self.replace[binaryop.left.name])
      
      if isinstance(binaryop.right, func.ID) and binaryop.right.name in self.replace:
        binaryop.right = func.Constant(self.replace[binaryop.right.name])

    self.generic_visit(binaryop)
  
  def visit_ArrayRef(self, arrayref):
    if not self.replace is None:
      if arrayref.subscript.name in self.replace:
        binaryop.subscript = func.Constant(self.replace[arrayref.subscript.name])

    self.generic_visit(arrayref)
  
  # def visit_FuncCall(self, func):

  def visit_ID(self, id):
    self.var_set.add(id.name)
    

class FunctionalTranslator:
  def __init__(self, ast, simplify):
    self.ast_c = AST_C(simplify)
    self.ast_c.visit(ast)
  
  def __str__(self):
    return str(self.ast_c.transform())