import os
import sys
import time
import random

class HerCodeInterpreter:
    def __init__(self, hercode_name):
        self.filename = f"{hercode_name}.txt"
        self.code_lines = []
        self.functions = {}
        self.entry_point = None
        self.variables = {}
        self.current_mood = None

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

            if line.startswith("function") or line.startswith("start:"):
                is_function = line.startswith("function")
                block_type_name = "function" if is_function else "start"

                func_name = ""
                if is_function:
                    parts = line.split()
                    if len(parts) < 2 or not parts[1].endswith(":"):
                        raise SyntaxError(f"Invalid function definition: {line}")
                    func_name = parts[1][:-1]

                block_lines_content = []
                nest_level = 1
                current_scan_idx = i + 1

                while current_scan_idx < len(self.code_lines):
                    scan_line = self.code_lines[current_scan_idx]
                    scanned_line_parts = scan_line.split()
                    scanned_line_keyword = scanned_line_parts[0] if scanned_line_parts else ""

                    if scanned_line_keyword == "if" or \
                       scanned_line_keyword == "when" or \
                       scanned_line_keyword == "repeat" or \
                       scanned_line_keyword == "function":
                        nest_level += 1
                    elif scanned_line_keyword == "end":
                        nest_level -= 1
                        if nest_level == 0:
                            break

                    block_lines_content.append(scan_line)
                    current_scan_idx += 1

                if nest_level != 0:
                    error_subject = f"function '{func_name}'" if is_function else block_type_name
                    raise SyntaxError(f"Missing 'end' for {error_subject} block starting at line {i+1}. Final nest_level={nest_level}.")

                parsed_body = self._parse_block_iteratively(block_lines_content)

                if is_function:
                    self.functions[func_name] = parsed_body
                else:
                    self.entry_point = parsed_body

                i = current_scan_idx + 1
            else:
                i += 1

    def _parse_statement(self, line):
        parts = line.split()
        keyword = parts[0]

        if keyword == "say":
            return ("say", line[len("say "):].strip())
        elif keyword == "let":
            var_name = parts[1]
            if len(parts) < 3 or parts[2] != "=":
                raise SyntaxError(f"Let statement missing '=' or value: {line}")
            value_expression = " ".join(parts[3:])
            return ("let", var_name, "=", value_expression)
        elif keyword == "get":
            # 支持宽松解析：get mood as "prompt"
            as_keyword_str = " as "
            lowered_line = line.lower()
            as_keyword_pos = lowered_line.find(as_keyword_str)
            
            if as_keyword_pos == -1:
                raise SyntaxError(f"Get statement missing 'as': {line} (Hint: use 'get mood as \"your prompt\"')")

            var_name_str = line[len("get "):as_keyword_pos].strip()
            if not var_name_str or " " in var_name_str:
                raise SyntaxError(f"Invalid variable name in get statement: '{var_name_str}' from line '{line}'")

            prompt_string = line[as_keyword_pos + len(as_keyword_str):].strip()
            
            # 自动去除错误的双引号配对问题
            if prompt_string.startswith('"') and not prompt_string.endswith('"'):
                prompt_string += '"'
            if prompt_string.endswith('"') and not prompt_string.startswith('"'):
                prompt_string = '"' + prompt_string

            # 检查是否完整包裹在引号中
            if not (prompt_string.startswith('"') and prompt_string.endswith('"')):
                raise SyntaxError(f"Prompt string must be wrapped in quotes: {prompt_string}")

            return ("get", var_name_str, "as", prompt_string)
        elif keyword == "repeat":
            times_keyword_str = " times"
            times_keyword_pos = line.rfind(times_keyword_str)
            if times_keyword_pos == -1 or not (line.endswith(times_keyword_str) or line[times_keyword_pos + len(times_keyword_str):].strip().startswith(":")):
                if line.strip().endswith("times:"):
                    times_keyword_pos = line.rfind("times:")
                else:
                    raise SyntaxError(f"Repeat statement missing 'times' keyword properly at the end: {line}")
            count_expression_str = line[len("repeat "):times_keyword_pos].strip()
            if not count_expression_str:
                raise SyntaxError(f"Missing count expression in repeat statement: {line}")
            return ("repeat", count_expression_str, "times", [])
        elif keyword == "call":
            func_name = parts[1]
            with_keyword_str = " with "
            with_keyword_pos = line.find(with_keyword_str)
            if with_keyword_pos != -1:
                args_str = line[with_keyword_pos + len(with_keyword_str):].strip()
                if not args_str:
                    raise SyntaxError(f"Missing arguments after 'with' in call statement: {line}")
                parsed_args = self._parse_comma_separated_args(args_str)
                return ("call", func_name, "with", parsed_args)
            return ("call", func_name)
        elif keyword == "because":
            return ("because", line[len("because "):].strip())
        elif keyword == "mood" or keyword == "tone":
            if len(parts) < 3 or parts[1] != "=":
                raise SyntaxError(f"Mood/Tone statement missing '=' or value: {line}")
            value_expression = " ".join(parts[2:])
            return (keyword, "=", value_expression)
        elif keyword == "wait":
            if len(parts) < 2:
                raise SyntaxError(f"Wait statement is incomplete: {line}")
            unit_string = "seconds"
            duration_expression = ""
            if len(parts) >= 2:
                if parts[-1].isalpha() and len(parts) > 2 :
                    unit_string = parts[-1]
                    duration_expression = " ".join(parts[1:-1])
                else:
                    duration_expression = " ".join(parts[1:])
            if not duration_expression:
                raise SyntaxError(f"Wait statement missing duration: {line}")
            return ("wait", duration_expression.strip(), unit_string)
        else:
            if len(parts) == 1 and not line.endswith(':'):
                return ("call", keyword)
            return ("unknown", line)

    def _parse_comma_separated_args(self, args_str):
        args = []
        current_arg = ""
        in_quotes = False
        quote_char = ''
        escape_next = False
        for char in args_str:
            if escape_next:
                current_arg += char
                escape_next = False
                continue
            if char == '\\':
                escape_next = True
                current_arg += char
                continue
            if char in ('"', "'"):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
            if char == ',' and not in_quotes:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        args.append(current_arg.strip())
        return [arg for arg in args if arg]

    def _parse_block_iteratively(self, block_lines):
        parsed_statements = []
        line_idx = 0
        while line_idx < len(block_lines):
            line = block_lines[line_idx]
            parts = line.split()
            if not parts:
                line_idx +=1
                continue
            keyword = parts[0]

            if keyword == "if" or keyword == "when":
                condition = " ".join(parts[1:])
                if not condition:
                    raise SyntaxError(f"Missing condition in {keyword} statement: {line}")
                nested_block_lines = []
                nest_level = 1
                current_nested_idx = line_idx + 1
                while current_nested_idx < len(block_lines):
                    current_nested_line = block_lines[current_nested_idx]
                    nested_parts = current_nested_line.split()
                    if not nested_parts:
                        current_nested_idx += 1
                        continue
                    nested_keyword = nested_parts[0]
                    if nested_keyword == "if" or nested_keyword == "when" or nested_keyword == "repeat":
                        nest_level += 1
                        nested_block_lines.append(current_nested_line)
                    elif nested_keyword == "end":
                        nest_level -= 1
                        if nest_level == 0:
                            break
                        else:
                            nested_block_lines.append(current_nested_line)
                    else:
                        nested_block_lines.append(current_nested_line)
                    current_nested_idx += 1
                if nest_level != 0:
                    raise SyntaxError(f"Missing 'end' for '{keyword}' block starting with: {line}")
                if_body = self._parse_block_iteratively(nested_block_lines)
                parsed_statements.append((keyword, condition, if_body))
                line_idx = current_nested_idx + 1
            elif keyword == "repeat":
                original_parsed_repeat_tuple = self._parse_statement(line)
                actual_count_expression = original_parsed_repeat_tuple[1]
                nested_block_lines = []
                nest_level = 1
                current_nested_idx = line_idx + 1
                while current_nested_idx < len(block_lines):
                    current_nested_line = block_lines[current_nested_idx]
                    nested_parts = current_nested_line.split()
                    if not nested_parts:
                        current_nested_idx += 1
                        continue
                    nested_keyword = nested_parts[0]
                    if nested_keyword == "if" or nested_keyword == "when" or nested_keyword == "repeat":
                        nest_level += 1
                        nested_block_lines.append(current_nested_line)
                    elif nested_keyword == "end":
                        nest_level -= 1
                        if nest_level == 0:
                            break
                        else:
                            nested_block_lines.append(current_nested_line)
                    else:
                        nested_block_lines.append(current_nested_line)
                    current_nested_idx += 1
                if nest_level != 0:
                    raise SyntaxError(f"Missing 'end' for 'repeat' block starting with: {line}")
                repeat_body = self._parse_block_iteratively(nested_block_lines)
                parsed_statements.append(("repeat", actual_count_expression, "times", repeat_body))
                line_idx = current_nested_idx + 1
            else:
                parsed_statements.append(self._parse_statement(line))
                line_idx += 1
        return parsed_statements

    def _evaluate_value(self, value_str):
        original_value_str = value_str.strip()
        if original_value_str.startswith("random "):
            try:
                list_str = original_value_str[len("random "):].strip()
                if not (list_str.startswith('[') and list_str.endswith(']')):
                    raise ValueError("Random options list must be enclosed in brackets [].")
                options_str = list_str[1:-1].strip()
                if not options_str: return ""
                options = []
                current_opt = ""
                in_quotes = False
                quote_char = ''
                for char_idx, char in enumerate(options_str):
                    if char in ('"', "'") and (char_idx == 0 or options_str[char_idx-1] != '\\'):
                        if not in_quotes: in_quotes = True; quote_char = char
                        elif in_quotes and char == quote_char: in_quotes = False
                    elif char == ',' and not in_quotes:
                        options.append(current_opt.strip().strip('"').strip("'"))
                        current_opt = ""
                        continue
                    current_opt += char
                options.append(current_opt.strip().strip('"').strip("'"))
                return random.choice(options) if options else ""
            except Exception as e:
                raise ValueError(f"Error parsing random expression '{original_value_str}': {e}")
        parts_to_concatenate = []
        current_segment = ""
        in_string_literal = False
        literal_quote_char = ''
        i = 0
        while i < len(original_value_str):
            char = original_value_str[i]
            if char in ('"', "'") and (i == 0 or original_value_str[i-1] != '\\'):
                if not in_string_literal: in_string_literal = True; literal_quote_char = char
                elif char == literal_quote_char: in_string_literal = False
                current_segment += char
            elif char == '+' and not in_string_literal:
                if current_segment.strip(): parts_to_concatenate.append(current_segment.strip())
                current_segment = ""
            else:
                current_segment += char
            i += 1
        if current_segment.strip(): parts_to_concatenate.append(current_segment.strip())
        if len(parts_to_concatenate) > 1 :
            evaluated_parts = [str(self._evaluate_single_value_token(part_str)) for part_str in parts_to_concatenate]
            return "".join(evaluated_parts)
        return self._evaluate_single_value_token(original_value_str)

    def _evaluate_single_value_token(self, token_str):
        token_str = token_str.strip()
        if token_str.startswith('"') and token_str.endswith('"'): return token_str[1:-1]
        if token_str.startswith("'") and token_str.endswith("'"): return token_str[1:-1]
        if token_str.lower() == "true": return True
        if token_str.lower() == "false": return False
        try:
            num = float(token_str)
            return int(num) if num.is_integer() else num
        except ValueError:
            if token_str in self.variables: return self.variables[token_str]
            raise NameError(f"Variable '{token_str}' not defined or value is not a recognized literal.")

    def execute(self):
        if not self.entry_point:
            raise Exception("No start block found.")
        for statement in self.entry_point:
            self.execute_statement(statement)

    def execute_statement(self, statement):
        keyword = statement[0]
        if keyword == "say":
            print(self._evaluate_value(statement[1]))
        elif keyword == "let":
            self.variables[statement[1]] = self._evaluate_value(statement[3])
        elif keyword == "get":
            self.variables[statement[1]] = input(self._evaluate_value(statement[3]) + " ")
        elif keyword == "if" or keyword == "when":
            condition_str = statement[1]
            body = statement[2]
            parts = condition_str.split()
            condition_met = False
            if len(parts) == 1: condition_met = bool(self._evaluate_value(parts[0]))
            elif len(parts) == 3:
                lhs = self._evaluate_value(parts[0])
                op = parts[1]
                rhs = self._evaluate_value(parts[2])
                if op == "==": condition_met = (lhs == rhs)
                elif op == "!=": condition_met = (lhs != rhs)
                else: raise ValueError(f"Unsupported operator in condition: {op}")
            else: raise ValueError(f"Invalid condition format: {condition_str}")
            if condition_met:
                for stmt in body: self.execute_statement(stmt)
        elif keyword == "repeat":
            count_str = statement[1]
            body = statement[3]
            try: count = int(self._evaluate_value(count_str))
            except ValueError: raise ValueError(f"Repeat count must be an integer, got: {count_str}")
            for _ in range(count):
                for stmt in body: self.execute_statement(stmt)
        elif keyword == "call":
            func_name = statement[1]
            evaluated_arg_list = []
            if len(statement) > 2 and statement[2] == "with":
                arg_strings_list = statement[3]
                for arg_str in arg_strings_list:
                    evaluated_arg_list.append(self._evaluate_value(arg_str))
            self.execute_function_body(func_name, evaluated_arg_list if evaluated_arg_list else None)
        elif keyword == "because": pass
        elif keyword == "mood" or keyword == "tone":
            self.current_mood = self._evaluate_value(statement[2])
        elif keyword == "wait":
            duration_str = statement[1]
            unit = statement[2].lower()
            try: duration = float(self._evaluate_value(duration_str))
            except ValueError: raise ValueError(f"Wait duration must be a number, got: {duration_str}")
            if unit == "seconds" or unit == "second": time.sleep(duration)
            elif unit == "milliseconds" or unit == "millisecond": time.sleep(duration / 1000.0)
            else: raise ValueError(f"Unsupported wait unit: {unit}. Use 'seconds' or 'milliseconds'.")
        elif keyword == "unknown":
            print(f"Warning: Executing unknown statement: {statement[1]}")

    def execute_function_body(self, func_name, args=None):
        if func_name not in self.functions:
            raise Exception(f"Function '{func_name}' not defined.")
        if args:
            # print(f"Calling function {func_name} with args: {args}") # Future: argument scoping
            pass
        body_statements = self.functions[func_name]
        for stmt in body_statements:
            self.execute_statement(stmt)

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
