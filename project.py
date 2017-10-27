from pycparser import parse_file
from minic.minic_ast import *
from minic.c_ast_to_minic import transform
import sys

sys.path.extend(['.', '..'])

#ast = parse_file('./tutorial.c')

def function_wrapper(filepath):
  function = ""
  with open(filepath, "r") as file:
    opening = "int main(int argc, char** argv) {"
    end = "}"
    function = opening + file.read() + end
    
  with open(filepath.replace(".txt", "_out.c"), "w") as file:
    file.write(function)

class BinaryOpVistor(NodeVisitor):
  def __init__(self):
    self.var_set = set()
  
  def visit_BinaryOp(self, binaryop):
    if isinstance(binaryop.left, ID):
      self.var_set.add(binaryop.left.name)
    
    if isinstance(binaryop.right, ID):
      self.var_set.add(binaryop.right.name)

class LHSPrinter(NodeVisitor):
  def __init__(self):
    self.written_set = set()
    self.var_set = set()

  def visit_Assignment(self, assignment):
    if isinstance(assignment.lvalue, ID):
      self.written_set.add(assignment.lvalue.name)
      self.var_set.add(assignment.lvalue.name)
    
    if isinstance(assignment.rvalue, BinaryOp):
      bov = BinaryOpVistor()
      bov.visit(assignment.rvalue)
      self.var_set.update(bov.var_set)
    
    if isinstance(assignment.rvalue, ArrayRef):
      self.var_set.add(assignment.rvalue.name.name)
      
if __name__ == "__main__":
  for i in range(1, 4):
    function_wrapper('./p3_input{}.txt'.format(i))
    mast = transform(parse_file('./p3_input{}_out.c'.format(i)))
    lhsp = LHSPrinter()
    print("p3_input{}.txt: ".format(i))
    lhsp.visit(mast)
    print("Written Variables: {} ".format(', '.join(lhsp.written_set)))
    print("All Variables: {} ".format(', '.join(lhsp.var_set)))

  


