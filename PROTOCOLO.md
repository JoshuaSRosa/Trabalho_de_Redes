# Especificação do Protocolo de Aplicação
## Jogo da Velha Multiplayer

Versão: 2.0
Data: [29/10/2026]

---

## 1. Visão geral

### 1.1 Transporte
- **Protocolo:** TCP (`SOCK_STREAM`)
- **Porta padrão:** 38912
- **Endereço padrão:** 127.0.0.1 (para testes locais)
- **Justificativa:** jogo em turnos, mensagens pequenas e de baixa frequência,
  necessidade de entrega confiável e ordenada. UDP não se justifica.

### 1.2 Codificação e framing
- **Formato:** JSON em UTF-8
- **Delimitador:** `\n` (uma mensagem por linha)
- **Framing:** TCP é um stream de bytes e não preserva fronteiras de mensagem.
  Cada endpoint mantém um buffer por conexão e processa uma mensagem por vez,
  separando no primeiro `\n` encontrado. Mensagens parciais (que chegam em
  múltiplos `recv`) são acumuladas até o `\n` chegar.

### 1.3 Arquitetura
- **Modelo:** cliente-servidor centralizado.
- **Participação:** servidor único, N clientes. O servidor gerencia filas de
  matchmaking, pareia jogadores com o mesmo `melhor_de`, e cada partida roda
  em uma thread dedicada.
- **Fluxo de mensagens:** o cliente inicia com um pedido de entrada na fila;
  o servidor responde com notificações (`na_fila`, `pareado`) e, durante a
  partida, com broadcast de `state` a cada jogada válida. O cliente envia
  jogadas; o servidor valida, aplica e notifica os dois participantes.

### 1.4 Modelo de comunicação
- **Request-response:** `fila` do cliente → `na_fila` ou `pareado` do servidor.
- **Server push:** `state`, `rodada_fim`, `fim`, `desconectou` são enviados
  pelo servidor sem solicitação explícita.
- **Turnos:** o servidor só consome jogadas da sessão do jogador atual. Uma
  jogada fora do turno é rejeitada com `erro`.

---

## 2. Formato das mensagens

### 2.1 Envelope
Toda mensagem é um objeto JSON com a seguinte forma genérica:

```json
{"tipo": "<identificador>", "<campo>": <valor>, ...}
```
O campo tipo identifica a mensagem. Os demais campos variam por tipo
(ver seção 3).

Exceção: durante uma partida, o cliente envia jogadas sem o campo
tipo (ver 3.1.2). O contexto determina que é uma jogada: o servidor só
consome a fila de partida do jogador da vez, e só espera {linha, coluna}.

### 2.2 Convenções de campo
| Nome | Tipo JSON | Descrição |
|---|---|---|
| `tipo` | string | Identificador da mensagem (ver seção 3) |
| `melhor_de` | integer | 1, 3 ou 5 — formato da série |
| `linha` | integer | Índice de linha, 0–2 |
| `coluna` | integer | Índice de coluna, 0–2 |
| `jogador` | string | `P1` ou `P2` |
| `jogador_atual` | string | `P1` ou `P2` |
| `oponente` | string | Identificação do oponente (formato `('IP', porta)`) |
| `tabuleiro` | array[3][3] | Matriz de strings: espaço vazio, `X`, `O` |
| `placar` | object | `{"jogador1": int, "jogador2": int, "empates": int}` |
| `partida_numero` | integer | Índice da rodada na série (0-indexado) |
| `finalizada` | boolean | `true` se a série terminou |
| `vencedor` | string | `P1`, `P2` ou `empate` |
| `msg` | string | Texto descritivo (para erros e avisos) |

### 2.3 Representação do tabuleiro
Matriz 3×3, indexação [linha][coluna]:

```json
[
  ["X", " ", "O"],
  [" ", "X", " "],
  ["O", " ", "X"]
]
```
" " — célula vazia

"X" — jogador X (sempre P1)

"O" — jogador O (sempre P2)

O símbolo X/O é atribuído pelo servidor e é fixo por jogador durante
toda a série. O jogador que começa alterna entre rodadas, mas o símbolo não.

## 3. Catálogo de mensagens
### 3.1 Cliente → Servidor
#### 3.1.1 fila
Solicita entrada na fila de matchmaking.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| `tipo` | sim | string | `fila` |
| `melhor_de` | não (default 3) | integer | Formato desejado: 1, 3 ou 5 |

Quando: logo após conectar, uma única vez.

Exemplo:

```json
{"tipo": "fila", "melhor_de": 3}
```
Respostas possíveis: na_fila (entrou, aguardando), pareado (par
formado imediatamente) ou erro (valor inválido de melhor_de).

#### 3.1.2 Jogada (sem tipo)
Envia uma jogada do jogador atual.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| linha | sim | integer | 0–2 |
| coluna | sim | integer | 0–2 |

Quando: durante uma partida, no turno do jogador.

Exemplo:

```json
{"linha": 1, "coluna": 1}
```
Respostas possíveis: state (jogada aceita, broadcast para os dois),
erro (jogada inválida, só para o remetente).

Nota de design: a jogada não carrega tipo nem jogador. A autoria é
inferida pelo servidor a partir da conexão de origem — o servidor só consome
da fila de partida do jogador da vez. Isso evita um cliente tentar jogar
como o adversário.

#### 3.1.3 saiu_fila (definida, não utilizada pelo cliente)
Solicita saída da fila antes de ser pareado.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "saiu_fila" |

Status: o servidor trata esta mensagem (roteador_sessao remove a sessão
da fila), mas o cliente atual não expõe a opção de cancelar a espera. Prevista
para expansão futura.

### 3.2 Servidor → Cliente
#### 3.2.1 na_fila
Confirmação de entrada na fila, quando o jogador ainda não foi pareado.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "na_fila" |
| melhor_de | sim | integer | Formato escolhido |
| msg | sim | string | Texto informativo ("aguardando oponente...") |

Quando: como resposta a fila, quando não há par disponível no momento.

Exemplo:

```json
{"tipo": "na_fila", "melhor_de": 3, "msg": "aguardando oponente..."}
```
#### 3.2.2 pareado
Informa que um par foi formado; a partida vai começar.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "pareado" |
| oponente | sim | string | Identificação do oponente (ex.: "('127.0.0.1', 54321)") |

Quando: enviado a ambos os jogadores no momento do pareamento, antes de
welcome e state.

Exemplo:

```json
{"tipo": "pareado", "oponente": "('127.0.0.1', 54321)"}
```
#### 3.2.3 welcome
Atribui o papel do jogador na partida (P1 ou P2).

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "welcome" |
| jogador | sim | string | "P1" ou "P2" |

Quando: imediatamente após pareado. Enviado a cada jogador com o seu
próprio papel.

Exemplo:

```json
{"tipo": "welcome", "jogador": "P1"}
```
#### 3.2.4 state
Estado atual da partida. Broadcast após cada jogada válida e no início.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "state" |
| tabuleiro | sim | array 3×3 | Estado atual |
| jogador_atual | sim | string | Quem deve jogar agora |
| placar | sim | object | Placar da série |
| partida_numero | sim | integer | Índice da rodada na série |
| finalizada | sim | boolean | true se a série terminou |

Quando: logo após welcome, e após cada jogada válida. Enviado aos dois
jogadores.

Exemplo:

```json
{
  "tipo": "state",
  "tabuleiro": [["X"," "," "],[" "," "," "],[" "," "," "]],
  "jogador_atual": "P2",
  "placar": {"jogador1": 0, "jogador2": 0, "empates": 0},
  "partida_numero": 0,
  "finalizada": false
}
```
Nota: quando finalizada for true, o cliente não deve renderizar
este state como se fosse um turno (o rodada_fim já mostrou o tabuleiro
final; o fim mostrará o resultado da série). O state final com
finalizada=true é enviado apenas para manter a simetria do fluxo de
broadcast.

#### 3.2.5 rodada_fim
Resultado de uma rodada (jogo individual da série).

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "rodada_fim" |
| vencedor | sim | string | "P1", "P2" ou "empate" |
| tabuleiro | sim | array 3×3 | Tabuleiro final da rodada |
| placar | sim | object | Placar atualizado |
| partida_numero | sim | integer | Índice da rodada que acabou |

Quando: quando uma rodada termina (vitória ou empate), antes do próximo
state (que será da rodada seguinte, se a série continuar).

Exemplo:

```json
{
  "tipo": "rodada_fim",
  "vencedor": "P1",
  "tabuleiro": [["X","X","X"],["O","O"," "],[" "," "," "]],
  "placar": {"jogador1": 1, "jogador2": 0, "empates": 0},
  "partida_numero": 0
}
```
#### 3.2.6 fim
Resultado final da série.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "fim" |
| vencedor | sim | string | "P1", "P2" ou "empate" |
| placar | sim | object | Placar final da série |
| tabuleiro | sim | array 3×3 | Tabuleiro final da última rodada |

Quando: após o término da série. Após este envio, o servidor encerra a
conexão dos dois jogadores.

Exemplo:

```json
{
  "tipo": "fim",
  "vencedor": "P1",
  "placar": {"jogador1": 2, "jogador2": 1, "empates": 0},
  "tabuleiro": [["X","X","O"],["O","O","X"],["X","O","X"]]
}
```
#### 3.2.7 erro
Mensagem de erro genérica.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "erro" |
| msg | sim | string | Descrição do erro |

Quando: jogada inválida, melhor_de inválido, mensagem fora do contexto
de fila, jogada sem linha/coluna.

Exemplos:

```json
{"tipo": "erro", "msg": "Casa já ocupada"}
{"tipo": "erro", "msg": "É a vez do seu adversário"}
{"tipo": "erro", "msg": "Jogada fora do tabuleiro"}
{"tipo": "erro", "msg": "melhor_de inválido: 2"}
{"tipo": "erro", "msg": "esperado 'fila' ou 'saiu_fila'"}
```

Comportamento: o cliente que recebeu o erro continua na mesma sessão
e pode tentar de novo (no caso de jogada inválida) ou escolher outro valor
(no caso de melhor_de inválido).

#### 3.2.8 desconectou
Informa que o oponente desconectou durante a partida.

| Campo | Obrigatório | Tipo | Descrição |
|---|---|---|---|
| tipo | sim | string | "desconectou" |

Quando: enviado ao jogador sobrevivente quando o parceiro cai. Após este
envio, o servidor encerra a conexão do sobrevivente (a partida é cancelada).

Exemplo:

```json
{"tipo": "desconectou"}
```
## 4. Sequências esperadas
### 4.1 Conexão e entrada na fila
```text
Cliente                          Servidor
  |                                 |
  |--- TCP connect ---------------->|
  |                                 |
  |--- {"tipo":"fila",             |
  |     "melhor_de":3} ------------>|
  |                                 |  (entra na fila 3)
  |<-- {"tipo":"na_fila",          |
  |     "melhor_de":3,             |
  |     "msg":"aguardando..."} ----|
  |                                 |
  (aguarda oponente)
```
### 4.2 Pareamento e início da partida
```text
Cliente A (aguardando)          Servidor              Cliente B (conecta)
  |                               |                    |
  |                               |<-- {"tipo":"fila", |
  |                               |     "melhor_de":3} |
  |                               |                    |
  |                               |  (pareia A com B)  |
  |<-- {"tipo":"pareado",...} ----|---- {"tipo":"pareado",...} -->|
  |<-- {"tipo":"welcome",         |                    |
  |     "jogador":"P1"} ----------|---- {"tipo":"welcome",        |
  |                               |     "jogador":"P2"} ---------->|
  |<-- {"tipo":"state",...} ------|---- {"tipo":"state",...} ---->|
```
### 4.3 Jogada válida
```text
P1                              Servidor              P2
  |                               |                    |
  |--- {"linha":1,"coluna":1} --->|                    |
  |                               |  (valida)          |
  |                               |  (aplica)          |
  |<-- {"tipo":"state",           |                    |
  |     "jogador_atual":"P2"} ----|---- {"tipo":"state",...} ---->|
```
Após a jogada, jogador_atual no state passa a ser "P2". O P1 vê
"Aguardando jogada de P2"; o P2 vê "SUA VEZ".

### 4.4 Fim de rodada (série continua)
```text
... (jogadas até vitória ou empate) ...

P1 (vence)                      Servidor              P2
  |--- {"linha":0,"coluna":2} --->|                    |
  |                               |  (aplica; detecta  |
  |                               |   fim de rodada)   |
  |<-- {"tipo":"rodada_fim",      |                    |
  |     "vencedor":"P1",          |                    |
  |     "tabuleiro":[final],      |                    |
  |     "placar":{...}} ----------|---- {"tipo":"rodada_fim",...} -->|
  |                               |                    |
  |  (série continua → nova rodada é iniciada)        |
  |<-- {"tipo":"state",           |                    |
  |     "partida_numero":1,...} --|---- {"tipo":"state",...} ---->|
```
### 4.5 Fim de série
```text
... (rodada final termina) ...

P1                              Servidor              P2
  |<-- {"tipo":"rodada_fim",...} -|---- {"tipo":"rodada_fim",...} -->|
  |<-- {"tipo":"state",           |                    |
  |     "finalizada":true} -------|---- {"tipo":"state",...} ---->|
  |<-- {"tipo":"fim",             |                    |
  |     "vencedor":"P1",...} -----|---- {"tipo":"fim",...} ---->|
  |                               |                    |
  |<-- (servidor fecha conexão) --|---- (fecha) ----->|
```
### 4.6 Desconexão durante partida
```text
P1                              Servidor              P2
  |                               |                    |
  | (P1 cai)                      |                    |
  |     X                         |                    |
  |                               |  (detecta via      |
  |                               |   sentinela ou     |
  |                               |   timeout ≤1s)     |
  |                               |                    |
  |                               |---- {"tipo":"desconectou"} --->|
  |                               |                    |
  |                               |---- (fecha) ----->|
```
O P2 recebe desconectou e encerra. A PARTIDA_MD é descartada — não há
reconexão (ver seção 5.6).

## 5. Comportamento diante de erros
### 5.1 JSON malformado
No servidor (thread_leitura): a exceção json.JSONDecodeError não
é capturada; a thread de leitura da sessão é encerrada, o que dispara
Sessao.encerrar() e a remoção do cliente. As demais sessões não são
afetadas. (Limitação conhecida: o tratamento ideal seria descartar a
mensagem e continuar; a versão atual opta pela terminação da sessão.)

No cliente (thread_recebimento): JSONDecodeError é capturado, e o
cliente encerra a thread de recebimento (a main percebe via ativo=False
na próxima interação).

### 5.2 Tipo desconhecido (fora de partida)
Quando a sessão está na fila (ainda não pareada) e recebe uma mensagem com
tipo diferente de "fila" ou "saiu_fila", o servidor responde:

```json
{"tipo": "erro", "msg": "esperado 'fila' ou 'saiu_fila'"}
```
A sessão continua viva; o cliente pode reenviar fila.

### 5.3 Jogada inválida
O servidor valida a jogada em JOGO_DA_VELHA.inserir_jogada. Se inválida:

| Causa | Mensagem de erro |
|---|---|
| Partida encerrada | "Partida já encerrada" |
| Fora do turno | "É a vez do seu adversário" |
| Linha/coluna fora de 0–2 | "Jogada fora do tabuleiro" |
| Casa ocupada | "Casa já ocupada" |

O cliente recebe erro e pode tentar de novo (o turno não avança).

### 5.4 Jogada malformada (sem linha ou coluna)
Se o cliente enviar um objeto sem linha ou coluna (por exemplo {}):

```json
{"tipo": "erro", "msg": "mensagem inválida"}
```
O turno não avança.

### 5.5 melhor_de inválido
Se o cliente enviar fila com melhor_de fora de {1, 3, 5}:

```json
{"tipo": "erro", "msg": "melhor_de inválido: 2"}
```
A sessão não entra na fila. O cliente pode enviar fila novamente com valor
válido (o cliente atual valida melhor_de localmente antes de enviar (aceita apenas 1, 3, 5) e nunca dispara este caso. O protocolo prevê retry: enviar fila novamente com valor válido.).

### 5.6 Desconexão
Detecção em até 1 segundo (via get(timeout=1) + flag viva) para quedas
bruscas; imediata via sentinela None para quedas graciosas. O sobrevivente
recebe desconectou e a partida é cancelada. Reconexão não é suportada
— o jogador que caiu teria que reabrir o cliente e entrar em uma nova fila
(nova partida, do zero).

### 5.7 Timeout de socket
Não há timeout de socket no cliente nem no servidor (excepto o
get(timeout=1) interno à thread de partida, que não afeta a conexão). Uma
conexão ociosa permanece aberta indefinidamente até um recv retornar b""
(queda graciosa) ou um sendall falhar (queda detectada no próximo envio).

## 6. Notas de implementação (opcional — para leitores do código)
Porta e endereço são hardcoded em servidor/main.py e cliente/main.py
(HOST = "127.0.0.1", PORT = 38912). Podem ser parametrizados via
variáveis de ambiente se necessário.

Número máximo de partidas simultâneas: ilimitado, limitado apenas por
recursos do sistema (uma thread por cliente, uma thread por partida).

Sem criptografia: as mensagens trafegam em texto claro (JSON sobre
TCP). Adequado ao escopo da disciplina; não usar em produção sem TLS.

