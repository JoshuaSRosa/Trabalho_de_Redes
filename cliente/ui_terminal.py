# Responsável pela inteface do terminal, realiza prints baseado nos estados
#recebidos como argumento, não modifica os estados

import os
from comum import protocolo as P

# Habilita sequências ANSI no terminal do Windows 10+
if os.name == "nt":
    os.system("")

# Códigos ANSI
R       = "\033[0m"       # reset
N       = "\033[1m"       # negrito
VERM    = "\033[31m"
AZUL    = "\033[34m"
VERDE   = "\033[32m"
AMAR    = "\033[33m"
CIANO   = "\033[36m"

SIMBOLO = {"P1": "X", "P2": "O"}


def limpar():
    # clear + home cursor — não spawna processo como os.system('cls')
    print("\033[2J\033[H", end="")


def _celula(c):
    if c == "X":
        return f"{VERM}{N} X {R}"
    if c == "O":
        return f"{AZUL}{N} O {R}"
    return "   "


def imprimir_tabuleiro(board):
    print(f"    {CIANO}1{R}   {CIANO}2{R}   {CIANO}3{R}")
    print("  +---+---+---+")
    for i, linha in enumerate(board):
        linha_txt = "|".join(_celula(c) for c in linha)
        print(f"{CIANO}{i+1}{R} |{linha_txt}|")
        if i < 2:
            print("  +---+---+---+")
    else:
        print("  +---+---+---+")


def renderizar(msg, estado):
    tipo = msg.get(P.TIPO)

    if tipo == P.PAREADO:
        limpar()
        print(f"{CIANO}[Oponente encontrado: {msg.get(P.OPONENTE, '?')}]{R}")
        print("[Aguardando início da partida...]")
        return

    if tipo == P.WELCOME:
        # Não limpa: PAREADO já limpou. Só complementa o cabeçalho.
        return

    if tipo == P.STATE:
        limpar()

        # cabeçalho
        meu = estado.meu_jogador or "?"
        simbolo = SIMBOLO.get(meu, "?")
        print(f"{N}=== Jogo {msg[P.PARTIDA_NUM] + 1} "
              f"===  Você: {CIANO}{meu} ({simbolo}){R}")
        pl = msg[P.PLACAR]
        print(f"Placar: P1 {VERM}{pl['jogador1']}{R} x "
              f"{AZUL}{pl['jogador2']}{R} P2   "
              f"(empates: {pl['empates']})")
        print()

        imprimir_tabuleiro(msg[P.TABULEIRO])
        print()

        vez = msg[P.JOGADOR_ATUAL]
        if vez == estado.meu_jogador:
            print(f"{VERDE}{N}>>> SUA VEZ ({vez}) <<<{R}")
        else:
            print(f"{AMAR}Aguardando jogada de {vez}...{R}")
        return

    if tipo == P.ERRO:
        # Não limpa: pode chegar enquanto o tabuleiro ainda está válido.
        print(f"{VERM}[ERRO] {msg.get(P.MSG, '')}{R}")
        return

    if tipo == P.FIM:
        limpar()
        print(f"{N}=== FIM DA SÉRIE ==={R}")
        v = msg[P.VENCEDOR]
        cor = VERDE if v == estado.meu_jogador else AMAR
        print(f"{cor}{N}Vencedor: {v}{R}")
        pl = msg[P.PLACAR]
        print(f"Placar final: P1 {pl['jogador1']} x {pl['jogador2']} P2 "
              f"(empates: {pl['empates']})")
        return

    if tipo == P.DESCONECTOU:
        print(f"{VERM}[Oponente desconectou]{R}")
        return

    if tipo == P.CHEIO:
        print(f"{VERM}[Servidor cheio]{R}")