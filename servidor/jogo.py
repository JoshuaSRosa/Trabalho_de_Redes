CASA_VAZIA = ' '  #Representação de uma casa Vazia no tabuleiro do jogo da velha

class JOGO_DA_VELHA:
    #características de uma partida de jogo da velha único
    def __init__(self, jogador1, jogador2):
        self.jogador1 = jogador1 # Player 1 - X
        self.jogador2 = jogador2 # Player 2 - O
        self.tabuleiro = [[CASA_VAZIA for i in range(3)] for i in range(3)] # Montagem do tabuleiro
        self.turno = 0 # Rodada atual da partida para alternar entre os jogadores
        self.encerrada = False # Verificadr se a partida terminou ou não
        self.vencedor = None # Vencedor da partida: P1, P2 ou empate

    def jogador_atual(self):
        return self.jogador1 if self.turno == 0 else self.jogador2

    def tabuleiro_cheio(self):
        return all(c != CASA_VAZIA for linha in self.tabuleiro for c in linha)

    def inserir_jogada(self, jogador, linha, coluna): # Função para inserir a jogada no tabuleiro

        #Verificação de erros na jogada
        if self.encerrada:
            raise ValueError("Partiada já encerrada") # Avisa que a partida já foi encerrada
        if  jogador != self.jogador_atual(): # Verifica se é a vez do jogador 
            raise ValueError("É a vez do seu adversário") # Avisa que não é a vez do jogador
        if not ((0 <= linha < 3) and (0 <= coluna < 3)): # Verifica se a jogada está dentro do tabuleiro
            raise ValueError("Jogada fora do tabuleiro") # Avisa que a jogada está fora do tabuleiro
        if self.tabuleiro[linha][coluna] != CASA_VAZIA: # Verifica se a casa está vazia
            raise ValueError("Casa já ocupada") # Avisa que a casa já está ocupada

        # Definição do símbolo do jogador atual
        if jogador == self.jogador1:
            símbolo = 'X' # Símbolo do jogador 1
        else:
            símbolo = 'O' # Símbolo do jogador 2

        # Inserção do símbolo no tabuleiro
        self.tabuleiro[linha][coluna] = símbolo

        # Verificação de vencedor ou empate após a jogada
        vencedor = self.verificar_vencedor()
        if vencedor is not None:
            self.encerrada = True
            self.vencedor = self.jogador1 if vencedor == 'X' else self.jogador2
        elif self.tabuleiro_cheio():
            self.encerrada = True
            self.vencedor = 'empate'
        else:
            self.turno = 1 - self.turno # Atualização do turno para o próximo jogador       

    def verificar_vencedor(self): # Função para verificar se há um vencedor na partida
        #Verifica se tem alguma linha completa com o mesmo símbolo
        for linha in self.tabuleiro:
            if (linha[0] == linha[1] == linha[2]) and (linha[0] != CASA_VAZIA): 
                return linha[0] # Retorna o símbolo do vencedor
            
        #Verfica se tem alguma coluna completa com o mesmo símbolo
        for j in range(3):
            if ((self.tabuleiro[0][j] == self.tabuleiro[1][j] == self.tabuleiro[2][j])
                    and (self.tabuleiro[0][j] != CASA_VAZIA)):
                return self.tabuleiro[0][j] # Retorna o símbolo do vencedor

        #Verifica se a diagonal principal está completa com o mesmo símbolo
        if (self.tabuleiro[0][0] == self.tabuleiro[1][1] == self.tabuleiro[2][2]) and (self.tabuleiro[0][0] != CASA_VAZIA):
            return self.tabuleiro[0][0] # Retorna o símbolo do vencedor

        #Verifica se a diagonal inversa está completa com o mesmo símbolo
        if (self.tabuleiro[0][2] == self.tabuleiro[1][1] == self.tabuleiro[2][0]) and (self.tabuleiro[0][2] != CASA_VAZIA):
            return self.tabuleiro[2][0] # Retorna o símbolo do vencedor
        
class PARTIDA_MD:
    # características de uma partida com melhor de 3 ou 5 partidas de jogo da velha
    # a cada partida da MD3 ou MD5, os jogadores alternam entre primeio e segundo jogador
    # abre uma nova PARTIDA a cada rodada da MD3/5
    def __init__(self, jogador1, jogador2, melhord):
        self.partidas = [] #Lista de partidas jogadas
        self.jogador1 = jogador1
        self.jogador2 = jogador2
        self.melhorD = melhord # Melhor de 3 ou 5
        self.vitorias_necessarias = (melhord // 2) + 1
        self.placar = {'jogador1': 0,'jogador2': 0,'empates': 0} #placar do jogo MD3/5
        self.winner = None # Vencedor do jogo MD3/5: P1, P2 ou empate
        self.finished = False # Verifica se a MD3/5 terminou ou não
        self.partida_atual = None # Partida atual da série MD3/5 atual
        self.partida_numero = 0 #Numeração da partida atual da série
        self.iniciar_proxima_partida() #Inicia a primeira partida da série

    def iniciar_proxima_partida(self): # Inicia a próxima partida
        # Alterna o símbolo dos jogadores a cada partida da MD3/5
        if self.partida_numero % 2 == 0:
            self.partida_atual = JOGO_DA_VELHA(self.jogador1,self.jogador2)
        else:
            self.partida_atual = JOGO_DA_VELHA(self.jogador2,self.jogador1)
        self.partidas.append(self.partida_atual) #Adiciona a partida a lista de histórico

    def jogador_atual(self):
        return self.partida_atual.jogador_atual() # Atualiza a jogada da partida atual
    
    def inserir_jogada(self, jogador, linha, coluna):
        if self.finished:
            raise ValueError("A série já foi encerrada")
        self.partida_atual.inserir_jogada(jogador, linha, coluna) # Realiza a jogada na partida atual
        if self.partida_atual.encerrada: # Garantia de partida finaizada antes do placar atualizar
            self.registrar_resultado()

    def registrar_resultado(self): # Atualiza o placar da partida MD3/5 após o término de uma partida
        self.partida_numero += 1 # Incrementa o número da partida
          
        if self.partida_atual.vencedor == self.partida_atual.jogador1:
            self.placar['jogador1'] += 1
        elif self.partida_atual.vencedor == self.partida_atual.jogador2:
            self.placar['jogador2'] += 1
        elif self.partida_atual.vencedor == 'empate':
            self.placar['empates'] += 1
            
        if (self.placar['jogador1'] >= self.vitorias_necessarias) or (self.placar['jogador2'] >= self.vitorias_necessarias):
            self.finished = True
            if self.placar['jogador1'] > self.placar['jogador2']:
                self.winner = self.jogador1
            elif self.placar['jogador2'] > self.placar['jogador1']:
                self.winner = self.jogador2

        elif(self.partida_numero >= self.melhorD):
            self.finished = True
            if self.placar['jogador1'] > self.placar['jogador2']:
                self.winner = self.jogador1
            elif self.placar['jogador2'] > self.placar['jogador1']:
                self.winner = self.jogador2
            else:
                self.winner = 'empate'
        else:       
            self.iniciar_proxima_partida()

if __name__ == "main":
    pass