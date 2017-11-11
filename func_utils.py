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