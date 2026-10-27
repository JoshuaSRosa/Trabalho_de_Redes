# Responsável pela inteface do terminal, realiza prints baseado nos estados
#recebidos como argumento, não modifica os estados

from comum import protocolo as P

def imprimir_tabuleiro(tabuleiro):
    for i, linha in enumerate(tabuleiro):
        print(" " + " | ".join(c if c != " " else "." for c in linha))
        if i < 2:
            print("---+---+---")
    print()

def renderizar(msg, estado):
    tipo = msg.get(P.TIPO)

    if tipo == P.PAREADO:
        print(f"\n[Oponente encontrado: {msg.get(P.OPONENTE, '?')}]")
        print("[Aguardando início da partida...]")
    elif tipo == P.WELCOME:
        print(f"\nVocê é {msg[P.JOGADOR]}")
    elif tipo == P.STATE:
        print(f"\n--- Jogo {msg[P.PARTIDA_NUM] + 1} ---")
        imprimir_tabuleiro(msg[P.TABULEIRO])
        print(f"Placar: {msg[P.PLACAR]}")
        vez = msg[P.JOGADOR_ATUAL]
        if vez == estado.meu_jogador:
            print(f">>> SUA VEZ ({vez}) <<<")
        else:
            print(f"Aguardando jogada de {vez}")
    elif tipo == P.ERRO:
        print(f"\n[ERRO] {msg.get(P.MSG, '')}")
    elif tipo == P.FIM:
        print(f"\n=== FIM DA SÉRIE ===")
        print(f"Vencedor: {msg[P.VENCEDOR]}")
        print(f"Placar final: {msg[P.PLACAR]}")
    elif tipo == P.DESCONECTOU:
        print("\n[Oponente desconectou]")
    elif tipo == P.CHEIO:
        print("\n[Servidor cheio]")