# Parte responsável por atualizar os estados do cliente conforme a chegada das mensagens do servidor

import threading
from comum import protocolo as P

class EstadoCliente:
    def __init__(self):
        self.meu_jogador = None   # None | "P1" | "P2"
        self.fase = "conectando"  # conectando | na_fila | pareado | jogando | finalizado
        self.minha_vez = threading.Event()
        self.ativo = True
        self.melhor_de = None
        self.ultima_partida_vista = None

    def entrar_na_fila(self, melhor_de):
        self.melhor_de = melhor_de
        self.fase = "na_fila"

    def processar(self, msg): #Atualiza o estado com base numa mensagem do servidor. Não imprime nada
        tipo = msg.get(P.TIPO)

        if tipo == P.PAREADO:
            self.fase = "pareado"
        elif tipo == P.WELCOME:
            self.meu_jogador = msg[P.JOGADOR]    
            self.fase = "jogando"
        elif tipo == P.STATE:
            self.fase = "jogando"
        elif tipo == P.ERRO: # jogada rejeitada —> libera a main para tentar de novo
            self.minha_vez.set() # impede o bloqueio em wait
        elif tipo == P.FIM:
            self.fase = "finalizado"
            self.ativo = False
            self.minha_vez.set() # impede o bloqueio em wait
        elif tipo == P.DESCONECTOU:
            self.fase = "finalizado"
            self.ativo = False
            self.minha_vez.set() # impede o bloqueio em wait
        elif tipo == P.CHEIO:
            self.fase = "finalizado"
            self.ativo = False
            self.minha_vez.set() # impede o bloqueio em wait

    def deve_acordar_main(self, msg):  #Retorna True se a main deve sair do wait() para processar.
        tipo = msg.get(P.TIPO)
        if tipo == P.STATE:
            # não acorda se a partida acabou (evita input após FIM)
            return (msg.get(P.JOGADOR_ATUAL) == self.meu_jogador and not msg.get(P.FINALIZADA, False))
        return tipo in (P.ERRO, P.FIM, P.DESCONECTOU, P.CHEIO)