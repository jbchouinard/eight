; Multiply a 16 bit int by an 8 bit int
begin:	lod a,[result + 1]
	add a,[num1 + 1]	; Add low-order byte
	sto [result + 1],a

	lod a,[result]
	adc a,[num1]		; Add high-order byte
	sto [result],a

	lod a,[num2 + 1]
	sub a, one		; Decrement second number
	sto [num2 + 1]

	jnz begin

	hlt

one:	01h
num1:	00h, a7h
num2:	00h, 1ch 		; first byte must be zero
result:	00h, 00h
