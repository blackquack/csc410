from minic.minic_ast import *
import func_ast as func

class AST_C(NodeVisitor):
  def __init__(self):
    self.written_set = set()
    self.var_set = set()

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
    # and update the written_set and var_set.
    if not condition.iftrue is None:
      iftrue_ast = AST_C()
      iftrue_ast.visit(condition.iftrue)

      self.written_set.update(iftrue_ast.written_set)
      self.var_set.update(iftrue_ast.var_set)
      if_written_set.update(iftrue_ast.written_set)

    if not condition.iffalse is None:
      iffalse_ast = AST_C()
      iffalse_ast.visit(condition.iffalse)

      self.written_set.update(iffalse_ast.written_set)
      self.var_set.update(iffalse_ast.var_set)
      if_written_set.update(iffalse_ast.written_set)
    
    # Create functional node
    lhs = func.ReturnTuple(if_written_set) if len(if_written_set) > 1 else func.ID(next(iter(if_written_set)))
    
    # Set the expression to be the same as the left hand side assignment if the iftrue or iffalse blocks are None.
    # Otherwise, set the tail binding's second expression to be the left hand side assignment and set the expression
    # as the binding of the associated branch.
    if condition.iftrue is None:
      iftrue_expr = lhs
    else:
      iftrue_ast.tail_binding.expr2 = lhs
      iftrue_expr = iftrue_ast.head_binding
    
    if condition.iffalse is None:
      iffalse_expr = lhs
    else:
      iffalse_ast.tail_binding.expr2 = lhs
      iffalse_expr = iffalse_ast.head_binding
    
    # Create functional condition node and binding
    if_expr = func.If(cond_expr, iftrue_expr, iffalse_expr)
    self.__create_binding(lhs, if_expr, None)

  def visit_Block(self, block):
    self.generic_visit(block)

  def visit_Assignment(self, assignment):
    self.generic_visit(assignment)

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
    self.var_set.add(id.name)
  
  def visit_ArrayRef(self, array_ref):
    self.var_set.add(array_ref.name.name)
    self.var_set.add(array_ref.subscript.name)
  
  def __create_binding(self, lhs, expr1, expr2):
    current_binding = func.Binding(lhs, expr1, expr2)
    if self.head_binding is None:
      self.head_binding = current_binding
    if not self.tail_binding is None:
      self.tail_binding.expr2 = current_binding
    self.tail_binding = current_binding

  # Transforms minic block into func_ast starting with FuncDef as parent node
  def transform(self):
    args_list = func.ArgsList(self.var_set)
    return_tuple = func.ReturnTuple(self.written_set)
    # For now only worry about let id = ... in ...
    self.tail_binding.expr2 = return_tuple
    return func.FuncDef(args_list, return_tuple, self.head_binding)

class FunctionalTranslator:
  def __init__(self, ast):
    self.ast_c = AST_C()
    self.ast_c.visit(ast)
  
  def __str__(self):
    return str(self.ast_c.transform())
