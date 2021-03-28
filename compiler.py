from compiler_lexer import CompilerLexer
from compiler_parser import CompilerParser
from compiler_analyzer import CompilerAnalyzer
from code_generator import CompilerCodeGenerator
import sys


if __name__ == '__main__':
    if len(sys.argv) == 3:
        lex = CompilerLexer()
        par = CompilerParser()
        with open(sys.argv[1], 'r') as input_file:
            parse_tree = par.parse(lex.tokenize(input_file.read()))
        # print("Parse Tree:")
        # for p in parse_tree:
        #     print(p)
        sem_analyzer = CompilerAnalyzer(parse_tree)
        generator = CompilerCodeGenerator(sem_analyzer)
        target_code = generator.generate()
        with open(sys.argv[2], 'w') as output_file:
            for command in target_code:
                output_file.write(command + "\n")
    else:
        print("Usage: python3 compiler.py [input file] [output file]")






