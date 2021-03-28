import sys

from sly import Parser
from compiler_lexer import CompilerLexer


class CompilerParser(Parser):
    tokens = CompilerLexer.tokens

    precedence = (  # lacznosc dzialan, wraz z ich rosnacym priorytetem
        ('left', PLUS, MINUS),
        ('left', MULTIPLY, DIVIDE),
        ('left', MOD)
    )

    # ------------------------------------------ program -----------------------------------------------

    @_('DECLARE declarations BEGIN commands END')
    def program(self, p):
        return ("program", p.declarations, p.commands)

    @_('BEGIN commands END')
    def program(self, p):
        return p.commands

    # ------------------------------------------ declarations ------------------------------------------
    @_('declarations COMMA PIDENTIFIER')
    def declarations(self, p):
        if p.declarations:
            p.declarations.append({'type': 'INT', 'name': p.PIDENTIFIER})
            return p.declarations

    @_('declarations COMMA PIDENTIFIER PAR_OPEN NUM COLON NUM PAR_CLOSE')
    def declarations(self, p):
        if p.declarations:
            p.declarations.append({'type': 'TAB', 'name': p.PIDENTIFIER, 'start': p.NUM0, 'stop': p.NUM1})
            return p.declarations

    @_('PIDENTIFIER')
    def declarations(self, p):
        return [{'type': 'INT', 'name': p.PIDENTIFIER}]

    @_('PIDENTIFIER PAR_OPEN NUM COLON NUM PAR_CLOSE')
    def declarations(self, p):
        return [{'type': 'TAB', 'name': p.PIDENTIFIER, 'start': p.NUM0, 'stop': p.NUM1}]

    # ------------------------------------------ commands -----------------------------------------------
    @_('commands command')
    def commands(self, p):
        p.commands.append(p.command)
        return p.commands

    @_('command')
    def commands(self, p):
        return [p.command]

    # ------------------------------------------ command -------------------------------------------------

    @_('identifier ASSIGN expression SEMICOLON')
    def command(self, p):
        return ('ASSIGN', p.identifier, p.expression)

    @_('IF condition THEN commands ELSE commands ENDIF')
    def command(self, p):
        return ('IF_ELSE', p.condition, p.commands0, p.commands1)

    @_('IF condition THEN commands ENDIF')
    def command(self, p):
        return ('IF', p.condition, p.commands)

    @_('WHILE condition DO commands ENDWHILE')
    def command(self, p):
        return ('WHILE', p.condition, p.commands)

    @_('REPEAT commands UNTIL condition SEMICOLON')
    def command(self, p):
        return ('REPEAT', p.condition, p.commands)

    @_('FOR PIDENTIFIER FROM value TO value DO commands ENDFOR')
    def command(self, p):
        return ('FOR_TO', p.PIDENTIFIER, p.value0, p.value1, p.commands)

    @_('FOR PIDENTIFIER FROM value DOWNTO value DO commands ENDFOR')
    def command(self, p):
        return ('FOR_DOWNTO', p.PIDENTIFIER, p.value0, p.value1, p.commands)

    @_('READ identifier SEMICOLON')
    def command(self, p):
        return ('READ', p.identifier)

    @_('WRITE value SEMICOLON')
    def command(self, p):
        return ('WRITE', p.value)

    # ------------------------------------------ expression ---------------------------------------------

    @_('value')
    def expression(self, p):
        return p.value

    @_('value PLUS value')
    def expression(self, p):
        return (p[1], p.value0, p.value1)

    @_('value MINUS value')
    def expression(self, p):
        return (p[1], p.value0, p.value1)

    @_('value MULTIPLY value')
    def expression(self, p):
        return (p[1], p.value0, p.value1)

    @_('value DIVIDE value')
    def expression(self, p):
        return (p[1], p.value0, p.value1)

    @_('value MOD value')
    def expression(self, p):
        return (p[1], p.value0, p.value1)

    # ------------------------------------------ condition ---------------------------------------------

    @_('value EQ value')
    def condition(self, p):
        return (p[1], p.value0, p.value1)

    @_('value INEQ value')
    def condition(self, p):
        return (p[1], p.value0, p.value1)

    @_('value LS value')
    def condition(self, p):
        return (p[1], p.value0, p.value1)

    @_('value GR value')
    def condition(self, p):
        return (p[1], p.value0, p.value1)

    @_('value LEQ value')
    def condition(self, p):
        return (p[1], p.value0, p.value1)

    @_('value GEQ value')
    def condition(self, p):
        return (p[1], p.value0, p.value1)

    # ------------------------------------------ value ----------------------------------------------------

    @_('NUM')
    def value(self, p):
        return ('NUM', p.NUM)

    @_('identifier')
    def value(self, p):
        return p.identifier

    # ------------------------------------------ identifier -----------------------------------------------

    @_('PIDENTIFIER')
    def identifier(self, p):
        return ('INT', p.PIDENTIFIER)

    @_('PIDENTIFIER PAR_OPEN PIDENTIFIER PAR_CLOSE')
    def identifier(self, p):
        return ('TAB', p.PIDENTIFIER0, ('INT', p.PIDENTIFIER1))

    @_('PIDENTIFIER PAR_OPEN NUM PAR_CLOSE')
    def identifier(self, p):
        return ('TAB', p.PIDENTIFIER, ('NUM', p.NUM))

    def error(self, p):
        if not p:
            print("Parser: Syntax error at the end of the file", file=sys.stderr)
        else:
            print(f"Parser: Syntax error around token: {p.value}", file=sys.stderr)
        exit(-1)
