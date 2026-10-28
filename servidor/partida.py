# Parte responsável por rodar uma PARTIDA_MD inteira
# consumindo das filas de entrada das duas sessões e
# produzindo as filas de saída

import threading
from .jogo import PARTIDA_MD
from .sessoes import Sessao
from comum import protocolo as P

def snapshot(md): # extrai o estado atual da partida
    p = md.partida_atual
    return {
        P.TIPO: P.STATE,
        P.TABULEIRO: p.tabuleiro,
        P.JOGADOR_ATUAL: md.jogador_atual(),
        P.PLACAR: dict(md.placar),
        P.PARTIDA_NUM: md.partida_numero,
        P.FINALIZADA: md.finished,
    }

def avisar_ambos(s1, s2, obj): # envia a mensagem para ambos os jogadores
    s1.enviar(obj)
    s2.enviar(obj)

# Roda Melhor De n entre s1(P1) e s2(P2). Retorna ao terminar a série MD-n
def thread_partida(s1: Sessao, s2: Sessao, melhor_de=3):
    md = PARTIDA_MD("P1","P2",melhor_de)

    # Mapa sessão -> label do jogador
    labels = {s1: "P1",s2: "P2"}
    # Mapa label -> sessão (para saber quem avisar)
    por_label = {"P1": s1, "P2": s2}

    # associa cada sessão à partida (para caso de desconexão)
    s1.partida = (threading.current_thread(), por_label)
    s2.partida = (threading.current_thread(),  por_label)

    # boa-vindas + estado incial
    s1.enviar({P.TIPO: P.WELCOME, P.JOGADOR: "P1"})
    s2.enviar({P.TIPO: P.WELCOME, P.JOGADOR: "P2"})
    avisar_ambos(s1,s2,snapshot(md))

    while not md.finished:
        # Saber de quem é a vez não basta: precisamos saber de quem LER.
        # Estratégia: leitura não-bloqueante alternada das duas filas.
        # Alternativa: ler sempre da sessão do jogador_atual.        
        atual_label = md.jogador_atual()
        atual_sessao = por_label[atual_label]
        outra_sessao = por_label["P2" if atual_label == "P1" else "P1"]

        # Consome as mensagens da sessao da vez (bloqueia até chegar a vez)
        msg = atual_sessao.fila_entrada.get()
        if msg is None:
            # se mensagem vazia -> encerra a sessao e avisa o outro
            outra_sessao.enviar({P.TIPO: P.DESCONECTOU})
            return

        linha = msg.get(P.LINHA)
        coluna = msg.get(P.COLUNA)
        if linha is None or coluna is None:
            atual_sessao.enviar({P.TIPO: P.ERRO, P.MSG: "mensagem inválida"})
            continue

        try:
            md.inserir_jogada(atual_label, linha, coluna)
        except ValueError as e:
            atual_sessao.enviar({P.TIPO: P.ERRO, P.MSG: str(e)})
            continue

        # jogada válida -> envia o STATE atualizado aos dois jogadores
        avisar_ambos(s1, s2, snapshot(md))

    # fim da séria da MD-n
    placar_final = dict(md.placar)
    vencedor = md.winner
    avisar_ambos(s1, s2, {
        P.TIPO: P.FIM,
        P.VENCEDOR: vencedor,
        P.PLACAR: placar_final,
    })