class Register:
    def __init__(self, name):
        self.name = name
        self.stored = None
        self.allocated = False


class CompilerCodeGenerator:
    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.target_code = []
        self.line_nr = 0
        self.linked = True
        regs = 'abcdef'
        self.register_desc = {r: Register(r) for r in regs}
        self.symbol_table = analyzer.symbol_table
        self.intermediate_code = analyzer.intermediate_code
        self.switch = {
            'ASSIGN': self.generate_assign,
            'LOAD': self.generate_load,
            'STORE': self.generate_store,
            'IF': self.generate_if,
            'GOTO': self.generate_jump,
            'WRITE': self.generate_write,
            'READ': self.generate_read,
            'INC': self.generate_inc,
            'DEC': self.generate_dec,
            '-': self.generate_sub,
            '+': self.generate_add,
            '*': self.generate_mult,
            '/': self.generate_div,
            '%': self.generate_mod,
        }
        self.operator = {
            '>': self.greater,
            '<': self.lesser,
            '>=': self.geq,
            '<=': self.leq,
        }

    def generate(self):
        for line in self.intermediate_code:
            self.line_nr += 1
            if line[0] in self.switch:
                self.switch[line[0]](line)
            else:
                self.target_code.append(line[0])
                self.clear_reg_tags()
        if self.linked:
            self.link_jumps()
        return self.target_code

    def link_jumps(self):
        labels = []
        for i in range(len(self.target_code)):
            line = self.target_code[i]
            if line[0] == 'J':
                s = line.split(' ')
                lab = s[-1]
                label = lab.split(':')[0]
                labels.append(label)
                direction = lab.split(':')[1]
                j = i
                counter = 0
                if direction == 'F':
                    while self.target_code[j] != label:
                        if self.target_code[j][0].isupper():
                            counter += 1
                        j += 1
                else:
                    while self.target_code[j] != label:
                        if self.target_code[j][0].isupper():
                            counter -= 1
                        j -= 1
                    counter += 1
                self.target_code[i] = self.target_code[i].replace(lab, str(counter))
        self.target_code = [x for x in self.target_code if x not in labels]

    def generate_assign(self, line):
        var = line[2]
        value = line[1]
        var_addr = self.analyzer.symbol_table[var]['address']
        reg_addr = self.get_register_for(var_addr)
        reg_val = self.get_register_for(value)
        self.store(reg_val, reg_addr)
        self.free_reg(reg_addr)
        self.free_reg(reg_val)

    def generate_load(self, line):
        addr = line[1]
        target = line[2]
        r1 = self.get_register_for(addr)
        r2 = self.get_register_for()
        self.load(r2, r1)
        self.set_stored(r2, target)
        self.free_reg(r1)
        self.free_reg(r2)

    def generate_store(self, line):
        addr = line[2]
        var = line[1]
        r1 = self.get_register_for(addr)
        r2 = self.get_register_for(var)
        self.store(r2, r1)
        self.free_reg(r2)
        self.free_reg(r1)

    def generate_read(self, line):
        addr = line[1]
        reg = self.get_register_for(addr)
        self.read(reg)
        self.free_reg(reg)

    def generate_write(self, line):
        addr = line[1]
        reg = self.get_register_for(addr)
        s = self.register_desc[reg].stored
        self.write(reg)
        self.free_reg(reg)

    def generate_if(self, line):
        condition = line[1]
        label = line[3]
        op = condition[1]
        arg1 = condition[0]
        arg2 = condition[2]
        if op == '=':
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            reg3 = self.get_register_for()
            r = self.inequal(reg1, reg2, reg3)
            self.jzero(r, label + ":F")
            self.free_reg(reg3)
        elif op == '!=':
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            reg3 = self.get_register_for()
            r = self.equal(reg1, reg2, reg3)
            l = self.analyzer.get_label()
            self.jzero(r, l + ":F")
            self.jump(label + ":F")
            self.target_code.append(l)
            self.free_reg(reg3)
        else:
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            r = self.operator[op](reg1, reg2)
            l = self.analyzer.get_label()
            self.jzero(r, l + ":F")
            self.jump(label + ":F")
            self.target_code.append(l)
        self.free_reg(reg1)
        self.free_reg(reg2)

    def generate_jump(self, line):
        self.jump(line[1])
        self.clear_reg_tags()

    def generate_inc(self, line):
        reg = self.get_register_for(line[1])
        self.inc(reg)
        self.free_reg(reg)

    def generate_dec(self, line):
        reg = self.get_register_for(line[1])
        self.dec(reg)
        self.free_reg(reg)

    def generate_sub(self, line):
        arg1 = line[1]
        arg2 = line[2]
        target = line[3]
        if arg2 == 1:
            reg1 = self.get_register_for(arg1)
            self.dec(reg1)
            self.set_stored(reg1, target)
        else:
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            self.sub(reg1, reg2)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
            self.free_reg(reg2)

    def generate_add(self, line):
        arg1 = line[1]
        arg2 = line[2]
        target = line[3]
        if arg1 == 1:
            reg1 = self.get_register_for(arg2)
            self.inc(reg1)
            self.set_stored(reg1, target)
        elif arg2 == 1:
            reg1 = self.get_register_for(arg1)
            self.inc(reg1)
            self.set_stored(reg1, target)
        else:
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            self.add(reg1, reg2)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
            self.free_reg(reg2)

    def generate_mult(self, line):
        arg1 = line[1]
        arg2 = line[2]
        target = line[3]
        if arg1 == 2:
            reg1 = self.get_register_for(arg2)
            self.shl(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg2 == 2:
            reg1 = self.get_register_for(arg1)
            self.shl(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg2 == 1:
            reg1 = self.get_register_for(arg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg1 == 1:
            reg1 = self.get_register_for(arg2)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        else:
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            reg3 = self.get_register_for()
            r = self.mult(reg1, reg2, reg3)
            self.set_stored(r, target)
            self.free_reg(reg1)
            self.free_reg(reg2)
            self.free_reg(reg3)

    def generate_div(self, line):
        arg1 = line[1]
        arg2 = line[2]
        target = line[3]
        if arg2 == 2:
            reg1 = self.get_register_for(arg1)
            self.shr(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg2 == 0:
            reg1 = self.get_register_for(arg1)
            self.clear_reg(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg1 == 0:
            reg1 = self.get_register_for(arg2)
            self.clear_reg(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg2 == 1:
            reg1 = self.get_register_for(arg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        else:
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            reg3 = self.get_register_for()
            reg4 = self.get_register_for()
            reg5 = self.get_register_for()
            q, r = self.div(reg1, reg2, reg3, reg4, reg5)
            self.set_stored(q, target)
            self.clear_tags(r)
            self.free_reg(reg1)
            self.free_reg(reg2)
            self.free_reg(reg3)
            self.free_reg(reg4)
            self.free_reg(reg5)

    def generate_mod(self, line):
        arg1 = line[1]
        arg2 = line[2]
        target = line[3]
        if arg2 == 0:
            reg1 = self.get_register_for(arg1)
            self.clear_reg(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg1 == 0:
            reg1 = self.get_register_for(arg2)
            self.clear_reg(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        elif arg2 == 1:
            reg1 = self.get_register_for(arg1)
            self.clear_reg(reg1)
            self.set_stored(reg1, target)
            self.free_reg(reg1)
        else:
            reg1 = self.get_register_for(arg1)
            reg2 = self.get_register_for(arg2)
            reg3 = self.get_register_for()
            reg4 = self.get_register_for()
            reg5 = self.get_register_for()
            q, r = self.div(reg1, reg2, reg3, reg4, reg5)
            self.set_stored(r, target)
            self.clear_tags(q)
            self.free_reg(reg1)
            self.free_reg(reg2)
            self.free_reg(reg3)
            self.free_reg(reg4)
            self.free_reg(reg5)

    # ------------------------------------------ registers allocation -----------------------------------------------

    def set_stored(self, reg, arg):
        self.register_desc[reg].stored = arg

    def empty(self, reg):
        self.register_desc[reg].allocated = False

    def clear_tags(self, reg):
        self.register_desc[reg].stored = None

    def free_reg(self, reg):
        arg = self.register_desc[reg].stored
        if isinstance(arg, int):
            self.empty(reg)
            return
        for line in self.intermediate_code[self.line_nr:]:
            if self.is_in(line, arg):
                return
            if line[0] == 'J':
                break
        self.clear_tags(reg)
        self.empty(reg)

    def is_in(self, arr, target):
        if not target:
            return False
        if target in arr:
            return True
        else:
            for e in arr:
                if isinstance(e, list):
                    return self.is_in(e, target)
        return False

    def get_register_for(self, arg=None):
        for r in self.register_desc:
            if self.register_desc[r].stored == arg and arg:
                self.register_desc[r].allocated = True
                return r
        for r in self.register_desc:
            if not self.register_desc[r].allocated:
                self.register_desc[r].allocated = True
                self.register_desc[r].stored = arg
                if isinstance(arg, int):
                    self.set_value(r, arg)
                return r
        print(f'ERROR FOR {arg}')

    def clear_reg_tags(self):
        for r in self.register_desc:
            self.register_desc[r].stored = None
            self.register_desc[r].allocated = False

    def set_value(self, reg, val):
        self.register_desc[reg].stored = val
        self.clear_reg(reg)
        if val == 0:
            return
        binary = str(bin(val))
        binary = binary[3:]
        self.inc(reg)
        for b in binary:
            if b == '1':
                self.shl(reg)
                self.inc(reg)
            else:
                self.shl(reg)

    # ------------------------------------------ target translation -----------------------------------------------

    def mov(self, target, source):
        self.clear_reg(target)
        self.set_stored(target, self.register_desc[source].stored)
        self.target_code.append(f'ADD {target} {source}')

    def equal(self, reg1, reg2, reg3):
        self.mov(reg3, reg1)
        self.sub(reg1, reg2)
        self.sub(reg2, reg3)
        self.add(reg1, reg2)
        self.clear_tags(reg1)
        self.clear_tags(reg2)
        return reg1  # !=0 means false

    def inequal(self, reg1, reg2, reg3):
        self.mov(reg3, reg1)
        self.sub(reg1, reg2)
        self.sub(reg2, reg3)
        self.add(reg1, reg2)
        self.clear_tags(reg1)
        self.clear_tags(reg2)
        return reg1

    def greater(self, reg1, reg2):
        self.sub(reg1, reg2)
        self.clear_tags(reg1)
        return reg1

    def lesser(self, reg1, reg2):
        self.sub(reg2, reg1)
        self.clear_tags(reg2)
        return reg2

    def geq(self, reg1, reg2):
        self.inc(reg1)
        return self.greater(reg1, reg2)

    def leq(self, reg1, reg2):
        self.inc(reg2)
        return self.lesser(reg1, reg2)

    def load(self, reg1, reg2):
        self.target_code.append(f'LOAD {reg1} {reg2}')

    def store(self, reg1, reg2):
        self.target_code.append(f'STORE {reg1} {reg2}')

    def jump(self, label):
        self.target_code.append(f'JUMP {label}')

    def jzero(self, reg, label):
        self.target_code.append(f'JZERO {reg} {label}')

    def jodd(self, reg, label):
        self.target_code.append(f'JODD {reg} {label}')

    def write(self, reg):
        self.target_code.append(f'PUT {reg}')

    def read(self, reg):
        self.target_code.append(f'GET {reg}')

    def inc(self, reg):
        self.target_code.append(f'INC {reg}')

    def dec(self, reg):
        self.target_code.append(f'DEC {reg}')

    def sub(self, reg1, reg2):
        self.target_code.append(f'SUB {reg1} {reg2}')

    def add(self, reg1, reg2):
        self.target_code.append(f'ADD {reg1} {reg2}')

    def mult(self, reg1, reg2, reg3):
        l1 = self.analyzer.get_label()
        l2 = self.analyzer.get_label()
        l3 = self.analyzer.get_label()
        l4 = self.analyzer.get_label()
        self.clear_reg(reg3)
        self.target_code.append(l1)
        self.jzero(reg2, l4+':F')
        self.jodd(reg2, l3+':F')
        self.target_code.append(l2)
        self.shr(reg2)
        self.shl(reg1)
        self.jump(l1+':B')
        self.target_code.append(l3)
        self.add(reg3, reg1)
        self.jump(l2+':B')
        self.target_code.append(l4)
        self.clear_tags(reg1)
        self.clear_tags(reg2)
        return reg3

    def div(self, a, b, c, res, a_cln):
        l1 = self.analyzer.get_label()
        l2 = self.analyzer.get_label()
        l3 = self.analyzer.get_label()
        l4 = self.analyzer.get_label()
        l5 = self.analyzer.get_label()

        self.clear_reg(res)
        self.clear_reg(a_cln)
        self.jzero(b, l4+":F")

        self.set_value(c, 1)
        self.mov(a_cln, a)
        self.shl(b)
        self.shl(c)

        self.target_code.append(l1)
        self.inc(a)
        self.sub(a, b)
        self.jzero(a, l2+':F')
        self.mov(a, a_cln)
        self.shl(b)
        self.shl(c)
        self.jump(l1+':B')

        self.target_code.append(l2)
        self.shr(c)
        self.shr(b)
        self.mov(a, a_cln)

        self.target_code.append(l3)
        self.jzero(c, l4+':F')
        self.inc(a)
        self.sub(a, b)
        self.jzero(a, l5+':F')
        self.sub(a_cln, b)
        self.add(res, c)
        self.target_code.append(l5)
        self.shr(b)
        self.shr(c)
        self.mov(a, a_cln)
        self.jump(l3+':B')
        self.target_code.append(l4)

        self.clear_tags(a)
        self.clear_tags(b)
        self.clear_tags(c)

        return res, a_cln

    def clear_reg(self, reg):
        self.target_code.append(f"RESET {reg}")

    def shl(self, reg):
        self.target_code.append(f'SHL {reg}')

    def shr(self, reg):
        self.target_code.append(f'SHR {reg}')
