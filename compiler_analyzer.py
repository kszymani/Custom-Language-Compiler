import sys


class CompilerAnalyzer:
    def __init__(self, syntax_tree):
        self.symbol_table = {}
        self.next_address_pointer = 0
        self.intermediate_code = []
        self.var_counter = 0
        self.label_counter = 0
        self.loop_counter = 0
        self.reverse_op = {
            '=': '!=',
            '!=': '=',
            '<': '>=',
            '>=': '<',
            '>': '<=',
            '<=': '>'
        }
        self.switch = {
            'ASSIGN': self.assign,
            'IF_ELSE': self.if_else,
            'IF': self.if_s,
            'WHILE': self.while_s,
            'REPEAT': self.repeat,
            'FOR_TO': self.for_to,
            'FOR_DOWNTO': self.for_downto,
            'READ': self.read,
            'WRITE': self.write
        }
        if syntax_tree[0] == 'program':
            self.declare(syntax_tree[1])
            commands = syntax_tree[2]
        else:
            commands = syntax_tree
        self.run(commands)
        self.intermediate_code.append(['HALT'])
        # print("Intermediate Code")
        # for p in self.intermediate_code:
        #     print(p)

    def run(self, commands):
        for c in commands:
            keyword = c[0]
            self.switch[keyword](c)

    def declare(self, variables):
        for var in variables:
            if var['name'] in self.symbol_table.keys():
                print(f"Analyzer: {var['name']} already declared", file=sys.stderr)
                exit(2)
            if var['type'] == 'INT':
                self.symbol_table[var['name']] = {'type': 'INT', 'address': self.next_address_pointer,
                                                  'is_iterator': None, 'initialised': False}
                self.next_address_pointer += 1
            else:
                if var['start'] > var['stop']:
                    print(f"Analyzer: Table {var['name']} declaration error:"
                          f"left end is higher than right one.", file=sys.stderr)
                    exit(2)
                self.symbol_table[var['name']] = {'type': 'TAB', 'address': self.next_address_pointer,
                                                  'start': var['start'], 'stop': var['stop']}
                self.next_address_pointer += var['stop'] - var['start'] + 1

    # ------------------------------------------ assign -----------------------------------------------
    def assign(self, command):
        left = command[1]
        right = command[2]
        self.is_left_valid(left)
        self.is_right_valid(right)
        te = self.evaluate_expression(right)
        if left[0] == 'INT':
            v = self.symbol_table[left[1]]
            v['initialised'] = True
            self.emit(['ASSIGN', te, left[1]])
        elif left[0] == 'TAB':
            index = left[2]
            tab = self.symbol_table[left[1]]
            if index[0] == 'INT':
                index_adr = self.symbol_table[index[1]]['address']
                t = self.get_temp_var()
                self.emit(['LOAD', index_adr, t])
                t1 = self.get_temp_var()
                self.emit(['+', tab['address'], t, t1])
                if tab['start'] != 0:
                    t2 = self.get_temp_var()
                    self.emit(['-', t1, tab['start'], t2])
                else:
                    t2 = t1
                self.emit(['STORE', te, t2])
            else:
                address = tab['address'] + index[1] - tab['start']
                self.emit(['STORE', te, address])

    def evaluate_expression(self, right):
        if right[0] == 'INT':
            t = self.get_temp_var()
            address = self.symbol_table[right[1]]['address']
            self.emit(['LOAD', address, t])
            return t
        elif right[0] == 'NUM':
            return right[1]
        elif right[0] == 'TAB':
            index = right[2]
            tab = self.symbol_table[right[1]]
            if index[0] == 'NUM':
                address = tab['address'] + index[1] - tab['start']
                t = self.get_temp_var()
                self.emit(['LOAD', address, t])
                return t
            else:
                index_adr = self.symbol_table[index[1]]['address']
                t = self.get_temp_var()
                self.emit(['LOAD', index_adr, t])
                t1 = self.get_temp_var()
                self.emit(['+', tab['address'], t, t1])
                if tab['start'] != 0:
                    t2 = self.get_temp_var()
                    self.emit(['-', t1, tab['start'], t2])
                else:
                    t2 = t1
                t3 = self.get_temp_var()
                self.emit(['LOAD', t2, t3])
                return t3
        else:  # expression
            op = right[0]
            arg1 = right[1]
            arg2 = right[2]
            t1 = self.evaluate_expression(arg1)
            t2 = self.evaluate_expression(arg2)
            t = self.get_temp_var()
            self.emit([op, t1, t2, t])
            return t

    def is_left_valid(self, left):
        if left[0] == 'TAB':
            if left[1] not in self.symbol_table.keys():
                print(f"Analyzer: Undeclared table {left[1]}", file=sys.stderr)
                exit(3)
            tab = self.symbol_table[left[1]]
            index = left[2]
            if tab['type'] == 'INT':
                print(f"Analyzer: {left[1]} is a variable, not table", file=sys.stderr)
                exit(3)
            if index[0] == 'INT' and index[1] not in self.symbol_table.keys():
                print(f"Analyzer: Attempt to assign value to table {left[1]} using "
                      f"undeclared variable: {index[1]}", file=sys.stderr)
                exit(3)
            elif index[0] == 'NUM':
                if index[1] < tab['start'] or index[1] > tab['stop']:
                    print(f"Analyzer: Attempt to assign value to table {left[1]} using "
                          f"value outside its range: {index[1]}", file=sys.stderr)
                    exit(3)
        elif left[0] == 'INT':
            if left[1] not in self.symbol_table.keys():
                print(f"Analyzer: Undeclared variable {left[1]}", file=sys.stderr)
                exit(3)
            var = self.symbol_table[left[1]]
            if var['type'] == 'TAB':
                print(f"Analyzer: {left[1]} is a table, not variable", file=sys.stderr)
                exit(3)
            if var['is_iterator']:
                print(f"Analyzer: Cannot modify loop iterator {left[1]}", file=sys.stderr)
                exit(3)
        else:  # NUM
            print(f"Analyzer: Left side of assign is a constant. ({left[1]})", file=sys.stderr)
            exit(3)

    def is_right_valid(self, right):
        if right[0] == 'TAB':
            if right[1] not in self.symbol_table.keys():
                print(f"Analyzer: Undeclared table {right[1]}", file=sys.stderr)
                exit(3)
            tab = self.symbol_table[right[1]]
            index = right[2]
            if tab['type'] == 'INT':
                print(f"Analyzer: {right[1]} is a variable, not table", file=sys.stderr)
                exit(3)
            if index[0] == 'INT':
                if index[1] not in self.symbol_table.keys():
                    print(f"Analyzer: Attempt to access table {right[1]} using "
                          f"undeclared variable: {index[1]}", file=sys.stderr)
                    exit(3)
                var = self.symbol_table[index[1]]
                if not var['initialised']:
                    print(f"Analyzer: Variable {index[1]} has no value assigned yet", file=sys.stderr)
                    exit(3)
            elif index[0] == 'NUM':
                if index[1] < tab['start'] or index[1] > tab['stop']:
                    print(f"Analyzer: Attempt to access table {right[1]} using "
                          f"value outside its range: {index[1]}", file=sys.stderr)
                    exit(3)
        elif right[0] == 'INT':
            if right[1] not in self.symbol_table.keys():
                print(f"Analyzer: Undeclared variable {right[1]}", file=sys.stderr)
                exit(3)
            var = self.symbol_table[right[1]]
            if var['type'] == 'TAB':
                print(f"Analyzer: {right[1]} is a table, not variable", file=sys.stderr)
                exit(3)
            if not var['initialised']:
                print(f"Analyzer: Variable {right[1]} has no value assigned yet", file=sys.stderr)
                exit(3)
        elif right[0] == 'NUM':
            return
        else:  # expression
            arg1 = right[1]
            arg2 = right[2]
            self.is_right_valid(arg1)
            self.is_right_valid(arg2)

    def is_declared(self, v):
        return v in self.symbol_table

    # ------------------------------------------ if_else -----------------------------------------------

    def if_s(self, command):
        condition = command[1]
        block = command[2]
        op = condition[0]
        arg1 = condition[1]
        arg2 = condition[2]
        self.is_value_valid(arg1)
        self.is_value_valid(arg2)
        t1 = self.evaluate_expression(arg1)
        t2 = self.evaluate_expression(arg2)
        rev_op = self.reverse_op[op]
        l1 = self.get_label()
        self.emit(['IF', [t1, rev_op, t2], 'GOTO', l1+':F'])
        self.run(block)
        self.emit([l1])

    def if_else(self, command):
        condition = command[1]
        block1 = command[2]
        block2 = command[3]
        op = condition[0]
        arg1 = condition[1]
        arg2 = condition[2]
        self.is_value_valid(arg1)
        self.is_value_valid(arg2)
        t1 = self.evaluate_expression(arg1)
        t2 = self.evaluate_expression(arg2)
        rev_op = self.reverse_op[op]
        l1 = self.get_label()
        l2 = self.get_label()
        self.emit(['IF', [t1, rev_op, t2], 'GOTO', l1+':F'])
        self.run(block1)
        self.emit(['GOTO', l2+':F'])
        self.emit([l1])
        self.run(block2)
        self.emit([l2])

    # ------------------------------------------ loops -----------------------------------------------
    def for_to(self, command):
        iterator = command[1]
        v0 = command[2]
        vk = command[3]
        block = command[4]
        self.is_value_valid(v0)
        self.is_value_valid(vk)
        self.declare_iterator(iterator, v0)
        if vk[0] != 'NUM':
            stop_val = self.get_loop_variable()
            self.declare_iterator(stop_val, vk)
        else:
            stop_val = vk[1]
        l1 = self.get_label()
        l2 = self.get_label()

        self.emit([l1])
        t = self.get_temp_var()
        self.emit(['LOAD', self.symbol_table[iterator]['address'], t])
        if vk[0] != 'NUM':
            t1 = self.get_temp_var()
            self.emit(['LOAD', self.symbol_table[stop_val]['address'], t1])
        else:
            t1 = stop_val
        self.emit(['IF', [t, '>', t1], 'GOTO', l2+':F'])
        self.run(block)
        t2 = self.get_temp_var()
        self.emit(['LOAD', self.symbol_table[iterator]['address'], t2])
        self.emit(['INC', t2])
        self.emit(['STORE', t2, self.symbol_table[iterator]['address']])
        self.emit(['GOTO', l1+':B'])
        self.emit([l2])
        self.remove_iterator(iterator)
        if vk[0] != 'NUM':
            self.remove_iterator(stop_val)

    def for_downto(self, command):
        iterator = command[1]
        v0 = command[2]
        vk = command[3]
        block = command[4]
        self.is_value_valid(v0)
        self.is_value_valid(vk)
        self.declare_iterator(iterator, v0)
        if vk[0] != 'NUM':
            stop_val = self.get_loop_variable()
            self.declare_iterator(stop_val, vk)
        else:
            stop_val = vk[1]
        l1 = self.get_label()
        l2 = self.get_label()

        self.emit([l1])
        t = self.get_temp_var()
        self.emit(['LOAD', self.symbol_table[iterator]['address'], t])
        if vk[0] != 'NUM':
            t1 = self.get_temp_var()
            self.emit(['LOAD', self.symbol_table[stop_val]['address'], t1])
        else:
            t1 = stop_val
        self.emit(['IF', [t, '<', t1], 'GOTO', l2+':F'])
        self.run(block)
        t2 = self.get_temp_var()
        self.emit(['LOAD', self.symbol_table[iterator]['address'], t2])
        self.emit(['IF', [t2, '=', 0], 'GOTO', l2 + ':F'])
        self.emit(['DEC', t2])
        self.emit(['STORE', t2, self.symbol_table[iterator]['address']])
        self.emit(['GOTO', l1+':B'])
        self.emit([l2])
        self.remove_iterator(iterator)
        if vk[0] != 'NUM':
            self.remove_iterator(stop_val)

    def declare_iterator(self, i, init_val):
        if self.is_declared(i):
            print(f"Analyzer: Duplicate declaration of iterator variable {i}", file=sys.stderr)
            exit(5)
        self.symbol_table[i] = {'type': 'INT', 'address': self.next_address_pointer,
                                'is_iterator': True, 'initialised': True}
        t = self.evaluate_expression(init_val)
        self.emit(['STORE', t, self.next_address_pointer])
        self.next_address_pointer += 1

    def remove_iterator(self, i):
        del self.symbol_table[i]
        self.next_address_pointer -= 1

    def while_s(self, command):
        condition = command[1]
        block = command[2]
        op = condition[0]
        arg1 = condition[1]
        arg2 = condition[2]
        self.is_value_valid(arg1)
        self.is_value_valid(arg2)
        rev_op = self.reverse_op[op]
        l1 = self.get_label()
        l2 = self.get_label()
        self.emit([l1])
        t1 = self.evaluate_expression(arg1)
        t2 = self.evaluate_expression(arg2)
        self.emit(['IF', [t1, rev_op, t2], 'GOTO', l2+':F'])
        self.run(block)
        self.emit(['GOTO', l1+':B'])
        self.emit([l2])

    def repeat(self, command):
        condition = command[1]
        block = command[2]
        op = condition[0]
        arg1 = condition[1]
        arg2 = condition[2]

        rev_op = self.reverse_op[op]
        l1 = self.get_label()
        self.emit([l1])
        self.run(block)
        self.is_value_valid(arg1)
        self.is_value_valid(arg2)
        t1 = self.evaluate_expression(arg1)
        t2 = self.evaluate_expression(arg2)
        self.emit(['IF', [t1, rev_op, t2], 'GOTO', l1+':B'])

    # ------------------------------------------- I/O ------------------------------------------------

    def read(self, command):
        var = command[1]
        if var[0] == 'NUM':
            print(f"Analyzer: {var[1]} is a constant, expected identifier", file=sys.stderr)
            exit(7)
        self.is_value_valid(var, to_be_read=True)
        if var[0] == 'INT':
            v = self.symbol_table[var[1]]
            address = v['address']
            self.emit(['READ', address])
            v['initialised'] = True
        else:
            index = var[2]
            tab = self.symbol_table[var[1]]
            if index[0] == 'NUM':
                address = tab['address'] + index[1] - tab['start']
                self.emit(['READ', address])
            else:
                index_adr = self.symbol_table[index[1]]['address']
                t = self.get_temp_var()
                self.emit(['LOAD', index_adr, t])
                t1 = self.get_temp_var()
                self.emit(['+', tab['address'], t, t1])
                if tab['start'] != 0:
                    t2 = self.get_temp_var()
                    self.emit(['-', t1, tab['start'], t2])
                else:
                    t2 = t1
                self.emit(['READ', t2])

    def write(self, command):
        val = command[1]
        self.is_value_valid(val)
        if val[0] == 'INT':
            v = self.symbol_table[val[1]]
            address = v['address']
            self.emit(['WRITE', address])
        elif val[0] == 'TAB':
            index = val[2]
            tab = self.symbol_table[val[1]]
            if index[0] == 'NUM':
                address = tab['address'] + index[1] - tab['start']
                self.emit(['WRITE', address])
            else:
                index_adr = self.symbol_table[index[1]]['address']
                t = self.get_temp_var()
                self.emit(['LOAD', index_adr, t])
                t1 = self.get_temp_var()
                self.emit(['+', tab['address'], t, t1])
                if tab['start'] != 0:
                    t2 = self.get_temp_var()
                    self.emit(['-', t1, tab['start'], t2])
                else:
                    t2 = t1
                self.emit(['WRITE', t2])
        else:  # NUM
            self.emit(['STORE', val[1], self.next_address_pointer])
            self.emit(['WRITE', self.next_address_pointer])

    # ------------------------------------------ utils -----------------------------------------------

    def is_value_valid(self, arg, to_be_read=False):
        if arg[0] == 'TAB':
            if arg[1] not in self.symbol_table.keys():
                print(f"Analyzer: Undeclared table {arg[1]}", file=sys.stderr)
                exit(3)
            tab = self.symbol_table[arg[1]]
            index = arg[2]
            if tab['type'] == 'INT':
                print(f"Analyzer: {arg[1]} is a variable, not table", file=sys.stderr)
                exit(3)
            if index[0] == 'INT':
                if index[1] not in self.symbol_table.keys():
                    print(f"Analyzer: Attempt to access table {arg[1]} using "
                          f"undeclared variable: {index[1]}", file=sys.stderr)
                    exit(3)
                var = self.symbol_table[index[1]]
                if not var['initialised']:
                    print(f"Analyzer: Variable {index[1]} has no value assigned yet", file=sys.stderr)
                    exit(3)
            elif index[0] == 'NUM':
                if index[1] < tab['start'] or index[1] > tab['stop']:
                    print(f"Analyzer: Attempt to access table {arg[1]} using "
                          f"value outside its range: {index[1]}", file=sys.stderr)
                    exit(3)
        elif arg[0] == 'INT':
            if arg[1] not in self.symbol_table.keys():
                print(f"Analyzer: Undeclared variable {arg[1]}", file=sys.stderr)
                exit(3)
            var = self.symbol_table[arg[1]]
            if var['type'] == 'TAB':
                print(f"Analyzer: {arg[1]} is a table, not variable", file=sys.stderr)
                exit(3)
            if not var['initialised'] and not to_be_read:
                print(f"Analyzer: Variable {arg[1]} has no value assigned yet", file=sys.stderr)
                exit(3)
        elif arg[0] == 'NUM':
            return

    def emit(self, command):  # emits three address code
        self.intermediate_code.append(command)

    def get_temp_var(self):
        self.var_counter += 1
        return 't'+str(self.var_counter)

    def get_label(self):
        self.label_counter += 1
        return 'label'+str(self.label_counter)

    def get_loop_variable(self):
        self.loop_counter += 1
        return 'loop'+str(self.loop_counter)








