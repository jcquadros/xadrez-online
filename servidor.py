import socket
import threading
import chess
import logging
import sys

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configurações do servidor
HOST = "127.0.0.1"
PORT = 65432

# Estrutura para armazenar salas de jogo
salas = {}
salas_lock = threading.Lock()

running = True

class SalaDeJogo:
    def __init__(self, nome):
        self.nome = nome
        self.jogadores = []
        self.tabuleiro = chess.Board()
        self.turno = 0  # Índice do jogador cujo turno é o atual (0 para Jogador 1, 1 para Jogador 2)
        self.lock = threading.Lock()
        logging.info(f"Sala '{nome}' criada.")
        self.gameover = False  

    def adicionar_jogador(self, jogador_socket):
        with self.lock:
            if len(self.jogadores) < 2:
                self.jogadores.append(jogador_socket)
                logging.info(f"Jogador adicionado à sala '{self.nome}'. Total: {len(self.jogadores)}")
                return len(self.jogadores) -1 # Retorna 1 para o primeiro jogador e 2 para o segundo
            return -1  # Indica que a sala já está cheia

    def remover_jogador(self, jogador_socket):
        with self.lock:
            if jogador_socket in self.jogadores:
                self.jogadores.remove(jogador_socket)
                logging.info(f"Jogador removido da sala '{self.nome}'. Restantes: {len(self.jogadores)}")

    def transmitir_movimento(self, remetente, movimento, jogador_id):
        if jogador_id != self.turno:
            remetente.sendall("Não é sua vez!\n".encode())
            return 
        
        if chess.Move.from_uci(movimento) in self.tabuleiro.legal_moves:
            self.tabuleiro.push(chess.Move.from_uci(movimento))
            logging.info(f"Movimento '{movimento}' registrado na sala '{self.nome}'.")
            
             # Verificar se há xeque
            if self.tabuleiro.is_check():
                logging.info(f"O rei do adversário está em xeque na sala '{self.nome}'.")
                for jogador in self.jogadores:
                    jogador.sendall("Aviso: Xeque!\n".encode())
            
            if self.tabuleiro.is_checkmate():
                vencedor = "Jogador 1" if self.turno == 1 else "Jogador 2"
                mensagem_final = f"Xeque-mate! {vencedor} venceu."
            elif self.tabuleiro.is_stalemate():
                mensagem_final = "Empate por afogamento!"
            elif self.tabuleiro.is_insufficient_material():
                mensagem_final = "Empate por falta de material suficiente!"
            elif self.tabuleiro.is_seventyfive_moves():
                mensagem_final = "Empate pela regra dos 75 movimentos!"
            elif self.tabuleiro.is_fivefold_repetition():
                mensagem_final = "Empate por repetição quíntupla!"
            else:
                mensagem_final = None  # O jogo continua
            
            # Se o jogo terminou, enviar mensagem e encerrar a sala
            if mensagem_final:
                logging.info(f"Jogo na sala '{self.nome}' terminou: {mensagem_final.strip()}")
                for jogador in self.jogadores:
                    jogador.sendall(f"{mensagem_final}\n{str(self.tabuleiro)}\n".encode())
                self.gameover = True
                print("Jogo terminou")
                return  

            # Alternar turno
            self.turno = 1 - self.turno  

            for i, jogador in enumerate(self.jogadores):
                try:
                    jogador.sendall(f"MOV:{movimento}\n{str(self.tabuleiro)}\n".encode())
                    jogador.sendall(("Sua vez!\n" if i == self.turno else "Aguarde o adversário...\n").encode())
                except:
                    self.remover_jogador(jogador)
                

        else:
            remetente.sendall("Movimento inválido. Tente novamente.\n".encode())


def handle_client(client_socket):
    try:
        client_socket.sendall("Digite o nome da sala para entrar: ".encode())
        sala_nome = client_socket.recv(1024).decode().strip()
        
        if not sala_nome:
            client_socket.sendall("Nome da sala inválido. Tente novamente.\n")
            client_socket.close()
            return

        with salas_lock:
            if sala_nome not in salas:
                salas[sala_nome] = SalaDeJogo(sala_nome)
            sala = salas[sala_nome]

        jogador_id = sala.adicionar_jogador(client_socket)
        if jogador_id == -1:
            client_socket.sendall("A sala esta cheia!\n".encode())
            logging.warning(f"Jogador tentou entrar em sala cheia: '{sala_nome}'.")
            client_socket.close()
            return

        client_socket.sendall(f"Entrou na sala {sala_nome} como Jogador {jogador_id +1}.\n".encode())

        logging.info(f"Jogador {jogador_id + 1} entrou na sala '{sala_nome}'. Aguardando adversário...")

        while len(sala.jogadores) < 2:
            pass  # Aguarda um segundo jogador

        logging.info(f"Jogo iniciado na sala '{sala_nome}'.")

        client_socket.sendall(f"Jogo iniciado!\n{str(sala.tabuleiro)}\n".encode())
        client_socket.sendall("Sua vez!\n".encode() if jogador_id == sala.turno else "Aguarde o adversário...\n".encode())

        while True:
            try:
                client_socket.sendall(f"Vez do Jogador {sala.turno + 1}.\n".encode())
                movimento = client_socket.recv(1024).decode().strip()

                if (len(sala.jogadores) < 2):
                    # Se o adversário desconectar, encerrar a sala
                    break

                if not movimento:
                    client_socket.sendall("Entrada vazia. Tente novamente.\n".encode())
                    continue
                logging.info(f"Recebido movimento: {movimento}")
                if movimento.startswith("MOV:"):
                    movimento_uci = movimento.split(":")[1].strip()
                    sala.transmitir_movimento(client_socket, movimento_uci, jogador_id)
                else:
                    client_socket.sendall("Entrada inválida. Envie um movimento no formato 'MOV:e2e4'.\n".encode())
                
                if sala.gameover:
                    print("Jogo terminou")
                    break
              
            except Exception as e:
                logging.error(f"Erro na comunicação com cliente: {e}")
                break
    except Exception as e:
        logging.error(f"Erro no cliente: {e}")
    finally:
        for jogador in sala.jogadores:
            if jogador != client_socket:
                jogador.sendall("O adversário desconectou. O jogo foi encerrado.\n".encode())
           
        sala.remover_jogador(client_socket)
        client_socket.close()     
        logging.info(f"Conexão com jogador encerrada na sala '{sala_nome}'.")
        if len(sala.jogadores) == 0:
            with salas_lock:
                if sala_nome in salas:
                    del salas[sala_nome]
                    logging.info(f"Sala '{sala_nome}' removida após o término da partida.")


def start_server():
    global running
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    logging.info(f"Servidor iniciado em {HOST}:{PORT}")

    try:
        while running:
            client_socket, _ = server_socket.accept()
            logging.info("Nova conexão aceita.")
            threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()
    except KeyboardInterrupt:
        logging.info("Servidor sendo encerrado devido a interrupção de teclado...")
    finally:
        # Fechar todas as conexões de clientes
        with salas_lock:
            for sala_nome, sala in list(salas.items()):
                for jogador in sala.jogadores:
                    try:
                        jogador.sendall("O servidor está sendo encerrado. Conexão finalizada.\n".encode())
                        jogador.close()
                    except Exception as e:
                        logging.error(f"Erro ao fechar conexão do jogador: {e}")
                del salas[sala_nome]
                logging.info(f"Sala '{sala_nome}' removida.")

        # Fechar o socket do servidor
        server_socket.close()
        logging.info("Servidor encerrado.")
        sys.exit(0)
    
if __name__ == "__main__":
    start_server()
