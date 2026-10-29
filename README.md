# Trabalho_de_Redes: Jogo da Velha Multiplayer

Trabalho da disciplina de Redes de Computadores — implementação de uma
aplicação de rede com sockets, protocolo de aplicação próprio e múltiplos
participantes.

---

## 1. Integrantes do grupo

| Nome completo | Matrícula |
|---|---|
| Joshua Souza da Rosa | 162584 |

---

## 2. Linguagem e versão

- **Linguagem:** Python 3
- **Versão mínima:** 3.8
- **Versão utilizada no desenvolvimento:** 3.11.9

**Justificativa da escolha:** a linguagem oferece suporte nativo a sockets
(`socket`), concorrência (`threading`), filas thread-safe (`queue`) e
serialização de dados (`json`), todas na biblioteca padrão. Isso permite
implementar a comunicação diretamente sobre a API de sockets, sem frameworks
que abstraiam os conceitos estudados na disciplina.

---

## 3. Descrição da aplicação

Jogo da Velha multiplayer com partidas em formato "melhor de N" (N ∈ {1, 3, 5}),
disputadas entre dois jogadores conectados a um servidor central.

### Funcionalidades implementadas

- **Múltiplos clientes simultâneos:** o servidor aceita conexões
  indefinidamente e cada cliente é atendido por um conjunto de threads
  dedicadas.
- **Matchmaking automático:** o cliente escolhe o formato (`melhor_de`) ao
  conectar e entra na fila correspondente. Dois jogadores com o mesmo
  `melhor_de` são pareados automaticamente.
- **Séries melhor de N:** o servidor controla o placar, alterna quem inicia
  cada rodada, e encerra a série quando um jogador atinge a maioria
  necessária (ou quando todas as rodadas foram jogadas — critério de
  desempate por maioria de vitórias).
- **Turnos com validação:** apenas o jogador da vez pode jogar. Jogadas
  fora do turno, em casas ocupadas, ou fora do tabuleiro são rejeitadas
  com mensagem de erro específica.
- **Sincronização entre jogadores:** cada jogada válida atualiza o estado
  de ambos os jogadores via broadcast.
- **Fim de rodada e fim de série:** o servidor envia o tabuleiro final de
  cada rodada (`rodada_fim`) e o resultado da série (`fim`) separadamente,
  permitindo ao cliente exibir ambos com clareza.
- **Tratamento de desconexão:** se um jogador cai durante a partida, o
  outro é notificado (`desconectou`) e o jogo é encerrado. A detecção
  ocorre imediatamente (queda graciosa via sentinela) ou em até 1 segundo
  (queda brusca via timeout).
- **Interface de terminal:** tabuleiro com cores ANSI, prompt de linha/coluna
  com validação local, mensagens de erro destacadas.

### Limitações conhecidas (não implementadas)

Documentadas por transparência, conforme priorização de escopo:

- **Reconexão:** não implementada. A queda de um jogador encerra a partida
  para ambos. Retomar a partida após reconectar era um objetivo planejado
  inicialmente, mas foi cortado por priorização da entrega completa dos
  requisitos obrigatórios. O enunciado exige "tratamento de desconexão"
  (cumprido), não reconexão persistente.
- **Tolerância a falhas do servidor:** o estado é mantido em memória; a
  queda do servidor encerra todas as partidas em andamento. Não havendo persistência
  em disco/banco ou banco.
- **Interface gráfica:** a interface é via terminal. Conforme o enunciado,
  "a complexidade da interface não será o foco da avaliação". Havia a ideia de
  montar um interface gráfica mais amigável, mas foi priorizada a funcionalidade,
  então a interface foi melhorada no terminal.
- **Tratamento de JSON malformado no servidor:** a thread de leitura da
  sessão é encerrada (a sessão cai), mas o servidor permanece funcional
  para as demais. Ver `PROTOCOLO.md`, seção 5.1.
- **Nova série sem reconectar:** após o fim de uma série, o cliente encerra
  a conexão. Para jogar novamente, é necessário reabrir o cliente.

---

## 4. Arquitetura escolhida

**Modelo:** cliente-servidor centralizado.

**Justificativa:** foi escolhido um servidor central por se tratar de um jogo de turnos
onde é necessário manter o estado da partida (tabuleiro, turno, placar), realizar o matchmaking
entre jogadores com mesma escolha de MD-N, e validar as jogadas antes de propagá-las aos dois participantes.
Uma arquitetura P2P dificultaria esses pontos sem trazer benefícios para um jogo de turnos.

### Organização do código
```text
Trabalho_de_Redes/
├── README.md ← este arquivo
├── PROTOCOLO.md ← especificação do protocolo de aplicação
├── requisitos.txt ← mapa de requisitos → implementação
├── requirements.txt ← dependências (nenhuma externa)
│
├── comum/
│   └── protocolo.py ← constantes compartilhadas (tipos, campos)
│
├── servidor/
│   ├── main.py ← accept loop + threads por sessão
│   ├── rede.py ← I/O puro (receber_linha, enviar)
│   ├── sessoes.py ← classe Sessao (filas, conn, partida)
│   ├── matchmaking.py ← filas por melhor_de, pareamento
│   ├── partida.py ← thread de partida (consome das filas)
│   └── jogo.py ← regras puras (PARTIDA_MD, JOGO_DA_VELHA)
│
└── cliente/
    ├── main.py ← setup, loop principal, thread de recebimento
    ├── rede.py ← I/O puro (receber_linha, enviar)
    ├── estado.py ← EstadoCliente (máquina de estados)
    └── ui_terminal.py ← renderização (cores ANSI, tabuleiro)
```


### Modelo de concorrência no servidor

Por conexão de cliente:
- **Thread de leitura:** lê do socket, acumula em buffer, parseia JSON,
  enfileira mensagens em `fila_entrada`.
- **Thread de escrita:** consome de `fila_saida` e envia ao socket.
- **Thread roteadora:** consome de `fila_entrada` enquanto o cliente está
  fora de partida (fase de matchmaking).

Por partida:
- **Thread da partida:** consome jogadas da `fila_partida` da sessão do
  jogador da vez, aplica no estado (`PARTIDA_MD`), e enfileira o novo
  estado nas `fila_saida` dos dois jogadores.

Toda comunicação entre threads é feita via `queue.Queue` (thread-safe por
construção). O estado da partida é privado à sua thread — nenhum lock é
necessário para o tabuleiro, pois apenas uma thread o manipula.

---

## 5. Protocolos de transporte

**Transporte:** TCP (`SOCK_STREAM`).

**Justificativa:** como o jogo escolhido acontece em turnos, com mensagens pequenas
e de baixa frequência, verificou-se necessidade de entrega confiável e ordenada. Jogadas perdidas
ou recebidas fora de ordem corromperiam o estado da partida. Além disso, no contexto do jogo, a latência
não é crítica, pois demoras de envio podem ser interpretadas como "o outro jogador demorou a realizar a jogada".
Não foi observado nenhum ganho em utilizar UDP ou mistura TCP/UDP para o caso da aplicação.

**Formato das mensagens:** JSON em UTF-8, delimitado por `\n`. A
especificação completa está em `PROTOCOLO.md`.

**Porta padrão:** 38912 (configurável em `servidor/main.py` e
`cliente/main.py`).

---

## 6. Bibliotecas utilizadas

**Todas as bibliotecas utilizadas são da standard library do Python 3.**
Nenhuma dependência externa é necessária.

| Biblioteca | Uso |
|---|---|
| `socket` | Sockets TCP nativos |
| `json` | Serialização/desserialização de mensagens |
| `threading` | Threads, locks, `Event` para sinalização |
| `queue` | Filas thread-safe (comunicação entre threads) |
| `os` | Detecção de sistema operacional (Windows ANSI) |
| `traceback` | Log de exceções no servidor (rede de segurança) |

**Não foram utilizados** frameworks que abstraiam sockets (como `asyncio`
para rede, `Twisted`, `websockets`, `aiohttp`). A comunicação foi
implementada diretamente sobre a API de sockets, conforme exigido pelo
enunciado.

---

## 7. Instruções de execução

### Pré-requisitos

- Python 3.8 ou superior instalado.
- Nenhuma biblioteca externa para instalar.

### Estrutura de execução

O projeto usa **imports relativos** entre os módulos internos de cada
pacote (`servidor/`, `cliente/`, `comum/`). Por isso, deve ser executado
**a partir da raiz do projeto**, com o modo módulo (`-m`) do Python.

### Iniciar o servidor

Em um terminal, na raiz do projeto:

```bash
python -m servidor.main
```
Saída esperada:
```bash
Servidor em 127.0.0.1:38912
```
Iniciar um cliente
Em outro terminal, na raiz do projeto:

```bash
python -m cliente.main
```
Ao iniciar, o cliente pede o formato da série:
```bash
Melhor de (1, 3 ou 5):
```
Digite 1, 3 ou 5 e pressione Enter. O cliente entra na fila e aguarda
um oponente.

Iniciar um segundo cliente
Repita o processo em um terceiro terminal. Quando o segundo cliente escolher
o mesmo melhor_de do primeiro, os dois serão pareados automaticamente e
a partida começa.

Durante o jogo
Quando for sua vez, o cliente exibe:

```bash
>>> SUA VEZ (P1) <<<
Linha (1-3): 
Coluna (1-3):
```
Digite a linha e a coluna (1 a 3) para jogar.

Encerrar:
Cliente: digite Ctrl+C ou feche a janela do terminal. Se for durante
uma partida, o oponente é notificado (desconectou).

Servidor: Ctrl+C no terminal do servidor.

---

## 8. Dependências necessárias
Nenhuma dependência externa. O projeto roda em Python 3.8+ puro.

O arquivo requirements.txt está presente apenas por convenção e contém
um comentário indicando que não há dependências a instalar.

---

## 9. Instruções para testar a aplicação
Cenário básico (MD1, dois jogadores)
Terminal 1: python -m servidor.main

Terminal 2: python -m cliente.main → escolha 1

Terminal 3: python -m cliente.main → escolha 1

Os dois clientes são pareados. P1 joga primeiro (X).

Jogue até alguém fechar uma linha, coluna ou diagonal, ou até o tabuleiro
encher (empate).

Ambos devem ver === RODADA 1: ... VENCEU === com o tabuleiro final,
seguido de === FIM DA SÉRIE === com o resultado e o placar.

As duas conexões são encerradas automaticamente.

Cenário MD3 (série com múltiplas rodadas)
Repita com melhor_de = 3. A série vai até um jogador atingir 2 vitórias
(ou até 3 rodadas jogadas, com desempate por maioria). A cada rodada, o
tabuleiro final é exibido (rodada_fim), seguido do início da próxima.

Cenário de múltiplas partidas simultâneas
Inicie 4 clientes, todos com melhor_de = 3. Os dois primeiros formam uma
partida; os dois seguintes formam outra, independente. As duas séries
correm em paralelo no servidor, sem interferência.

Cenário de matchmaking por formato
Inicie 2 clientes com melhor_de = 1 e 2 com melhor_de = 3. Cada par se
forma apenas com jogadores do mesmo formato — os pares não se misturam.

Cenário de jogada inválida
Durante uma partida, quando for sua vez, tente:

Jogar em uma casa já ocupada pelo adversário (Casa já ocupada).

Digitar uma coordenada fora do intervalo 1–3 (Fora do tabuleiro (use 1-3)).

Digitar uma letra em vez de número (Digite números de 1 a 3).

O turno não avança e você pode tentar de novo.

Cenário de desconexão
Durante uma partida, pressione Ctrl+C em um dos clientes. O outro deve
receber [Oponente desconectou] e encerrar a conexão em até ~1 segundo.

Cenário de mensagem de fila
Inicie um único cliente. Ele deve exibir:

```bash
Conectado. Entrando na fila (melhor de 3)...
[Na fila (melhor de 3) — aguardando oponente...]
```
E ficar aguardando até um segundo cliente entrar com o mesmo melhor_de.

---

## 10. Declaração sobre o uso de Inteligência Artificial
Durante o desenvolvimento deste trabalho, foram utilizadas ferramentas de
Inteligência Artificial (assistentes conversacionais) como apoio para:

Discussão de design de arquitetura e de protocolo de aplicação;

Revisão de código e identificação de bugs;

Depuração de erros de concorrência (sincronização entre threads, uso
correto de filas e sentinelas);

Elaboração e revisão da documentação (README, PROTOCOLO.md,
requisitos.txt).

Toda a lógica de jogo, a arquitetura de rede, o protocolo de comunicação
e a implementação foram desenvolvidos por mim, com a IA atuando como
ferramenta de apoio e não como autora. Compreendo integralmente o
funcionamento do código entregue e sou capaz de justificar cada decisão de
projeto.

O código-fonte foi integralmente lido, testado e validado por mim antes
da entrega. As decisões de arquitetura (TCP vs UDP, cliente-servidor vs
P2P, thread por cliente vs thread por partida) foram avaliadas e justificadas
conscientemente, conforme documentado nas seções 4 e 5 deste README e no
PROTOCOLO.md.

---

## Referências
PROTOCOLO.md — especificação completa do protocolo de aplicação
(formato das mensagens, catálogo, sequências, tratamento de erros).

requisitos.txt — mapa de requisitos do enunciado → implementação no
código.
