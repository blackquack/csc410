from pycparser import parse_file
from minic.minic_ast import *
from minic.c_ast_to_minic import transform
import sys
import os

sys.path.extend(['.', '..'])

#ast = parse_file('./tutorial.c')

def function_wrapper(filepath):
  function = ""
  with open(filepath, "r") as file:
    opening = "int main(int argc, char** argv) {"
    end = "}"
    function = opening + file.read() + end

  output_c = filepath + "_out.c" if not filepath.endswith(".txt") else filepath.replace(".txt", "_out.c")

  with open(output_c, "w") as file:
    file.write(function)
  
  return output_c

class AST_C(NodeVisitor):
  def __init__(self):
    self.written_set = set()
    self.var_set = set()

  def visit_Assignment(self, assignment):
    if isinstance(assignment.lvalue, ID):
      self.written_set.add(assignment.lvalue.name)
    
    if isinstance(assignment.rvalue, BinaryOp):
      self.visit_BinaryOp(assignment.rvalue)
    
    if isinstance(assignment.rvalue, ArrayRef):
      self.var_set.add(assignment.rvalue.name.name)
  
  def visit_BinaryOp(self, binaryop):
    self.generic_visit(binaryop)
  
  def visit_ID(self, id):
    self.var_set.add(id.name)
  
class FunctionalTranslator:
  def __init__(self, ast):
    self.ast_c = AST_C()
    self.ast_c.visit(ast)
  
  def __str__(self):
    params = ', '.join(self.ast_c.var_set)
    return_tuple = '(' + ', '.join(self.ast_c.written_set) + ')'
    return "fun block_function({}) returns {}".format(params, return_tuple)

if __name__ == "__main__":
  directory_path = "./inputs"
  directory = os.fsencode(directory_path)
  for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if not filename.endswith("_out.c"):
      output_c = function_wrapper(os.path.join(directory_path, filename))
      mast = transform(parse_file(output_c))
      ftranslator = FunctionalTranslator(mast)
      print("{} ".format(filename))
      print("Function Prototype: {}".format(ftranslator))
