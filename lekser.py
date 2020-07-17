import ply.lex as lex

tokens = (
	'DECLARE', 'BEGIN', 'END','COMMA', 'SEMICOLON', 'NEG',
	'NUM',
	'PLUS', 'MINUS', 'MULT', 'DIV', 'MOD',
	'EQ', 'NEQ', 'LEQ', 'GEQ', 'LE', 'GE',
	'ASSIGN',
	'LBR','RBR','COLON',
	'IF', 'THEN', 'ELSE', 'ENDIF',
	'DO',
		'FOR', 'FROM', 'TO', 'DOWNTO', 'ENDFOR',
		'WHILE', 'ENDDO', 'ENDWHILE',
	'READ', 'WRITE',
	'ID'
)


t_ignore_COM = r'\[[^\]]*\]'
t_DECLARE	= r'DECLARE'
t_BEGIN		= r'BEGIN'
t_END		= r'END'
t_COMMA = r','
t_SEMICOLON	= r';'
t_NEG =r'\-'

def t_NUM(t):
	r'\d+'
	t.value = int(t.value)	
	return t

t_PLUS	= r'PLUS'
t_MINUS	= r'MINUS'
t_MULT	= r'TIMES'
t_DIV	= r'DIV'
t_MOD	= r'MOD'
t_EQ	= r'EQ'
t_NEQ	= r'NEQ'
t_LEQ	= r'LEQ'
t_GEQ	= r'GEQ'
t_LE	= r'LE'
t_GE	= r'GE'
t_ASSIGN = r'ASSIGN'
t_LBR	= r'\('
t_RBR	= r'\)'
t_COLON	= r':'
t_IF	= r'IF'
t_THEN	= r'THEN'
t_ELSE	= r'ELSE'
t_ENDIF	= r'ENDIF'
t_DO	= r'DO'
t_FOR	= r'FOR'
t_FROM	= r'FROM'
t_TO	= r'TO'
t_DOWNTO= r'DOWNTO'
t_ENDFOR= r'ENDFOR'
t_WHILE	= r'WHILE'
t_ENDDO	= r'ENDDO'
t_ENDWHILE= r'ENDWHILE'
t_READ	= r'READ'
t_WRITE	= r'WRITE'
t_ID = r'[_a-z]+'

def t_newline(t):
	r'\r?\n+'
	t.lexer.lineno += len(t.value)

t_ignore  = ' \t'

def t_error(t):
	print("Illegal character '%s'" % t.value[0])
	t.lexer.skip(1)

lexer = lex.lex()