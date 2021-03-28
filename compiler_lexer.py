from sly import Lexer


class CompilerLexer(Lexer):
    errored = False
    tokens = {
        ASSIGN,
        SEMICOLON,
        COLON,
        COMMA,
        PIDENTIFIER,
        NUM,
        DECLARE,
        BEGIN,
        END,
        PAR_OPEN,
        PAR_CLOSE,
        IF,
        THEN,
        ELSE,
        ENDIF,
        WHILE,
        DO,
        ENDWHILE,
        REPEAT,
        UNTIL,
        FOR,
        FROM,
        TO,
        DOWNTO,
        ENDFOR,
        READ,
        WRITE,
        PLUS,
        MINUS,
        MULTIPLY,
        DIVIDE,
        MOD,
        EQ,
        INEQ,
        LS,
        GR,
        LEQ,
        GEQ,
    }

    ignore = ' \t'

    @_(r'\[[^\[]*\]')
    def ignore_comment(self, t):
        self.lineno += t.value.count('\n')

    @_(r'\n+')
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')

    @_(r'[0-9]+')
    def NUM(self, t):
        t.value = int(t.value)
        return t

    PIDENTIFIER = r'[_a-z]+'

    ASSIGN = r':='
    INEQ = r'!='
    LEQ = r'<='
    GEQ = r'>='
    EQ = r'='
    MOD = r'%'
    LS = r'<'
    GR = r'>'
    PLUS = r'\+'
    MINUS = r'\-'
    MULTIPLY = r'\*'
    DIVIDE = r'\/'

    SEMICOLON = r';'
    COLON = r':'
    COMMA = r','
    PAR_OPEN = r'\('
    PAR_CLOSE = r'\)'

    DECLARE = r'DECLARE'
    BEGIN = r'BEGIN'
    ENDWHILE = r'ENDWHILE'
    WHILE = r'WHILE'
    ENDIF = r'ENDIF'
    IF = r'IF'
    THEN = r'THEN'
    ELSE = r'ELSE'
    REPEAT = r'REPEAT'
    UNTIL = r'UNTIL'
    DOWNTO = r'DOWNTO'
    ENDFOR = r'ENDFOR'
    FOR = r'FOR'
    FROM = r'FROM'
    END = r'END'
    DO = r'DO'
    TO = r'TO'
    READ = r'READ'
    WRITE = r'WRITE'

    def error(self, t):
        print(f'Lexer: Error in line {self.lineno}: bad character {t.value[0]}')
        self.index += 1
