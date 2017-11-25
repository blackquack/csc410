from pycparser import parse_file
from minic.c_ast_to_minic import transform
from transform_func import *
from func_utils import function_wrapper
import sys
import os

if __name__ == "__main__":
  directory_path = "./inputs/checkin5_inputs"
  directory = os.fsencode(directory_path)
  for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if not filename.endswith("_out.c"):
      output_c = function_wrapper(os.path.join(directory_path, filename))
      mast = transform(parse_file(output_c))
      print("File: {} \nInput:".format(filename))
      with open(os.path.join(directory_path, filename), 'r') as fin:
        print(fin.read())
      ftranslator = FunctionalTranslator(mast, False)
      print("No Simplification Output:\n{}\n".format(ftranslator))
      ftranslator = FunctionalTranslator(mast, True)
      print("With Simplification Output:\n{}\n----------".format(ftranslator))