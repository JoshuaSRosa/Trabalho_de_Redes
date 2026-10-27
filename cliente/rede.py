# Parte responsável por transporte:
# - Receber bytes e montar as mensagens JSON
# - Converter mensagens JSON em bytes e enviar

import json

# Funções para comunicação com os sockets

# Função para extrair linha do buffer
def receber_linha(conn, buffer):
    while b"\n" not in buffer:
        data = conn.recv(4096)   # Recebe o dado
        if data == b"":          # Se não houver dado
            return None, buffer  # Retorna None e o buffer
        buffer += data           # Se houver dado, atualiza o buffer com o novo dado

    linha, buffer = buffer.split(b"\n", 1)   # Extrai uma linha do buffer
    return json.loads(linha.decode("utf-8")), buffer # Retorna o dado extraído decodificado, e o buffer atualizado

# Função para enviar um dado codificado
def enviar(conn, obj):
    try:
        conn.sendall((json.dumps(obj) + "\n").encode("utf-8")) # Converte o (obj_json + "\n") para bytes e envia pelo socket conn
        return True   # retorna True
    except OSError:   # caso de erro, não envia e retorna False
        return False