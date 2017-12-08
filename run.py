import sys
import os
sys.path.extend(['.', '..'])

from pycparser import parse_file
from minic.c_ast_to_minic import transform
from transform_func import *
from func_utils import function_wrapper

def get_output(directory_path):
  output_c = function_wrapper(directory_path)
  mast = transform(parse_file(output_c))
  print("File: {} \nInput:".format(directory_path.split('/'[-1])))
  with open(directory_path, 'r') as fin:
    print(fin.read())
  ftranslator = FunctionalTranslator(mast, True)
  print("Output:\n{}\n----------".format(ftranslator))

if __name__ == "__main__":
  if len(sys.argv) == 3 and sys.argv[1] == '-f':
    get_output(sys.argv[2])
  else:
    directory_path = "./inputs/final_inputs"
    directory = os.fsencode(directory_path)
    for file in os.listdir(directory):
      filename = os.fsdecode(file)
      if not filename.endswith("_out.c"):
        get_output(os.path.join(directory_path, filename))