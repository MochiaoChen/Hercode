import os
import sys

class HerCodeInterpreter:
    def __init__(self, hercode_name):
        self.filename = f"{hercode_name}.txt"
        self.code_lines = []
        self.functions = {}
        self.entry_point = None

    def load_code(self):
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"File '{self.filename}' not found.")
        with open(self.filename, encoding='utf-8') as f:
            self.code_lines = [
                line.strip() for line in f.readlines()
                if line.strip() and not line.strip().startswith('#')
            ]

    def parse(self):
        i = 0
        while i < len(self.code_lines):
            line = self.code_lines[i]
            if line.startswith("function"):
                func_name = line.split()[1][:-1]  # 去掉冒号
                i += 1
                body = []
                while not self.code_lines[i].startswith("end"):
                    body.append(self.code_lines[i])
                    i += 1
                self.functions[func_name] = body
            elif line.startswith("start:"):
                self.entry_point = []
                i += 1
                while not self.code_lines[i].startswith("end"):
                    self.entry_point.append(self.code_lines[i])
                    i += 1
            i += 1

    def execute(self):
        if not self.entry_point:
            raise Exception("No start block found.")
        for call in self.entry_point:
            self.execute_function(call)

    def execute_function(self, func_name):
        if func_name not in self.functions:
            raise Exception(f"Function '{func_name}' not defined.")
        for line in self.functions[func_name]:
            if line.startswith("say "):
                content = line[len("say "):].strip()
                print(content.strip('"'))
            elif self.functions.get(line):
                self.execute_function(line)


def main():
    if len(sys.argv) != 2:
        print("Usage: python hercode_runner.py <hercode_filename_without_txt>")
        sys.exit(1)

    hercode_name = sys.argv[1]
    interpreter = HerCodeInterpreter(hercode_name)
    try:
        interpreter.load_code()
        interpreter.parse()
        interpreter.execute()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
