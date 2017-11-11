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
          self.expr(orig.left.__class__ ,orig.left), 
          self.expr(orig.right.__class__, orig.right)))
      }.get(_class)(value)

  def visit_Assignment(self, assignment):
    self.generic_visit(assignment)

    expr1 = self.expr(assignment.rvalue.__class__, assignment.rvalue)

    if isinstance(assignment.lvalue, ID):
      written_var = func.ID(assignment.lvalue.name)
      self.written_set.add(assignment.lvalue.name)
    else:
      written_var = func.ArrayRef(assignment.lvalue.name.name, assignment.lvalue.subscript.name)
      self.written_set.add(assignment.lvalue.name.name)

    current_binding = func.Binding(written_var, expr1, None)
    if self.head_binding is None:
      self.head_binding = current_binding
    if not self.tail_binding is None:
      self.tail_binding.expr2 = current_binding
    self.tail_binding = current_binding

  def visit_BinaryOp(self, binaryop):
    self.generic_visit(binaryop)
    
  def visit_ID(self, id):
    self.var_set.add(id.name)
  
  def visit_ArrayRef(self, array_ref):
    self.var_set.add(array_ref.name.name)
    self.var_set.add(array_ref.subscript.name)

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
