print("Tabla de verdad")
print("P | Q | ¬P | P∧Q | P∨Q | P→Q | P↔Q")


# ---------- Combinacion 1: P = True , Q = True ----------
P = True
Q = True

# Negacion (¬P): es verdadera solo cuando P es falsa
if P:
    no_P = False
else:   
    no_P = True

# Conjuncion (P ∧ Q): verdadera solo si P y Q son verdaderas
p_y_q = P and Q

# Disyuncion (P ∨ Q): si P es verdadera, ya es verdadera;
# si P es falsa, entonces depende de Q
if P:
    p_o_q = True
else:
    p_o_q = Q

# Condicional (P → Q): "si P entonces Q"
# si P es verdadera, debe cumplirse Q; si P es falsa, es verdadera
if P:
    p_si_q = Q
else:
    p_si_q = True

# Bicondicional (P ↔ Q): verdadera cuando P y Q valen lo mismo
p_bic_q = (P == Q)

print(P, "|", Q, "|", no_P, "|", p_y_q, "|", p_o_q, "|", p_si_q, "|", p_bic_q)


# ---------- Combinacion 2: P = True , Q = False ----------
P = True
Q = False

if P:
    no_P = False
else:
    no_P = True

p_y_q = P and Q

if P:
    p_o_q = True
else:
    p_o_q = Q

if P:
    p_si_q = Q
else:
    p_si_q = True

p_bic_q = (P == Q)

print(P, "|", Q, "|", no_P, "|", p_y_q, "|", p_o_q, "|", p_si_q, "|", p_bic_q)


# ---------- Combinacion 3: P = False , Q = True ----------
P = False
Q = True

if P:
    no_P = False
else:
    no_P = True

p_y_q = P and Q

if P:
    p_o_q = True
else:
    p_o_q = Q

if P:
    p_si_q = Q
else:
    p_si_q = True

p_bic_q = (P == Q)

print(P, "|", Q, "|", no_P, "|", p_y_q, "|", p_o_q, "|", p_si_q, "|", p_bic_q)


# ---------- Combinacion 4: P = False , Q = False ----------
P = False
Q = False

if P:
    no_P = False
else:
    no_P = True

p_y_q = P and Q

if P:
    p_o_q = True
else:
    p_o_q = Q

if P:
    p_si_q = Q
else:
    p_si_q = True

p_bic_q = (P == Q)

print(P, "|", Q, "|", no_P, "|", p_y_q, "|", p_o_q, "|", p_si_q, "|", p_bic_q)