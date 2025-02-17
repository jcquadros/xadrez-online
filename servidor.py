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

def formatar_tabuleiro(tabuleiro):
    """
    Formata um tabuleiro de xadrez para uma representação em string.
    Args:
        tabuleiro (object): Objeto que representa o tabuleiro de xadrez e possui um método __str__() 
                            que retorna a representação do tabuleiro em string.
    Returns:
        str: Uma string formatada do tabuleiro de xadrez, com colunas e linhas numeradas.
    """
    
    colunas = "  a b c d e f g h"
    tabuleiro_str = tabuleiro.__str__().split("\n")
    tabuleiro_formatado = "\n".join([f"{8 - i} {linha}" for i, linha in enumerate(tabuleiro_str)])
    return f"{colunas}\n{tabuleiro_formatado}\n  a b c d e f g h"

class SalaDeJogo:
    """
    Classe que representa uma sala de jogo de xadrez.
    Atributos:
        nome (str): Nome da sala de jogo.
        jogadores (list): Lista de sockets dos jogadores na sala.
        tabuleiro (chess.Board): Objeto que representa o tabuleiro de xadrez.
        turno (int): Índice do jogador cujo turno é o atual (0 para Jogador 1, 1 para Jogador 2).
        lock (threading.Lock): Lock para garantir a segurança em operações de múltiplas threads.
        gameover (bool): Indica se o jogo terminou.
    Métodos:
        __init__(self, nome):
            Inicializa uma nova instância da sala de jogo com o nome fornecido.
        adicionar_jogador(self, jogador_socket):
            Adiciona um jogador à sala de jogo.
            Retorna o índice do jogador adicionado ou -1 se a sala já estiver cheia.
        remover_jogador(self, jogador_socket):
            Remove um jogador da sala de jogo.
        transmitir_movimento(self, remetente, movimento, jogador_id):
            Transmite um movimento de xadrez para a sala de jogo.
            Verifica a validade do movimento, atualiza o tabuleiro e alterna o turno.
            Envia mensagens apropriadas aos jogadores sobre o estado do jogo.
    """
    def __init__(self, nome):
        self.nome = nome
        self.jogadores = []
        self.tabuleiro = chess.Board()
        self.turno = 0  # Índice do jogador cujo turno é o atual (0 para Jogador 1, 1 para Jogador 2)
        self.lock = threading.Lock()
        logging.info(f"Sala '{nome}' criada.")
        self.gameover = False  

    def adicionar_jogador(self, jogador_socket):
        """
        Adiciona um jogador à sala, se houver espaço disponível.
        Args:
            jogador_socket (socket): O socket do jogador a ser adicionado.
        Returns:
            int: O índice do jogador na lista de jogadores (0 para o primeiro jogador, 1 para o segundo jogador).
             Retorna -1 se a sala já estiver cheia.
        """
        
        with self.lock:
            if len(self.jogadores) < 2:
                self.jogadores.append(jogador_socket)
                logging.info(f"Jogador adicionado à sala '{self.nome}'. Total: {len(self.jogadores)}")
                return len(self.jogadores) -1 #
            return -1  

    def remover_jogador(self, jogador_socket):
        """
        Remove um jogador da lista de jogadores da sala.
        Args:
            jogador_socket (socket): O socket do jogador a ser removido.
        Returns:
            None
        """
        
        with self.lock:
            if jogador_socket in self.jogadores:
                self.jogadores.remove(jogador_socket)
                logging.info(f"Jogador removido da sala '{self.nome}'. Restantes: {len(self.jogadores)}")
    
  

    def transmitir_movimento(self, remetente, movimento, jogador_id):
        """
        Transmite o movimento de um jogador para todos os jogadores na sala e atualiza o estado do jogo.
        Args:
            remetente (socket.socket): O socket do jogador que enviou o movimento.
            movimento (str): O movimento no formato UCI (Universal Chess Interface).
            jogador_id (int): O ID do jogador que fez o movimento.
        Returns:
            None
        Comportamento:
            - Verifica se é a vez do jogador que enviou o movimento.
            - Verifica se o movimento é legal.
            - Atualiza o tabuleiro com o movimento.
            - Verifica condições de xeque, xeque-mate, empate por afogamento, falta de material suficiente, regra dos 75 movimentos e repetição quíntupla.
            - Envia mensagens apropriadas aos jogadores dependendo do estado do jogo.
            - Alterna o turno entre os jogadores.
            - Envia o estado atualizado do tabuleiro para todos os jogadores.
            - Encerra a sala se o jogo terminou.
        """
        
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
                    jogador.sendall(f"{mensagem_final}\n{formatar_tabuleiro(self.tabuleiro.unicode())}\n".encode())
                self.gameover = True
                print("Jogo terminou")
                return  

            # Alternar turno
            self.turno = 1 - self.turno  

            for i, jogador in enumerate(self.jogadores):
                try:
                    jogador.sendall(f"MOV:{movimento}\n{formatar_tabuleiro(self.tabuleiro.unicode())}\n".encode())
                    jogador.sendall(("Sua vez!\n" if i == self.turno else "Aguarde o adversário...\n").encode())
                except:
                    self.remover_jogador(jogador)
                

        else:
            remetente.sendall("Movimento inválido. Tente novamente.\n".encode())


def handle_client(client_socket):
    """
    Lida com a comunicação com um cliente conectado.
    Esta função gerencia a interação com um cliente, incluindo a entrada em uma sala de jogo,
    o tratamento de movimentos de jogo e a gestão do estado do jogo. Ela garante que o cliente seja
    devidamente adicionado a uma sala de jogo, espera por um oponente e processa os movimentos do jogo
    até que o jogo termine ou o cliente se desconecte.
    Args:
        client_socket (socket.socket): O objeto socket que representa a conexão do cliente.
    Raises:
        Exception: Se houver um erro na comunicação com o cliente.
    A função realiza os seguintes passos:
    1. Solicita ao cliente que insira o nome de uma sala.
    2. Valida o nome da sala e entra em uma sala existente ou cria uma nova.
    3. Adiciona o cliente como jogador na sala.
    4. Aguarda um segundo jogador entrar na sala.
    5. Inicia o jogo e gerencia o loop do jogo, processando os movimentos do cliente.
    6. Lida com a desconexão do cliente e limpa a sala, se necessário.
    """
    
    try:
        client_socket.sendall("Digite o nome da sala para entrar: ".encode())
        sala_nome = client_socket.recv(1024).decode().strip()
        
        if not sala_nome:
            client_socket.sendall("Nome da sala inválido. Tente novamente.\n")
            client_socket.close()
            return

        with salas_lock:
            if sala_nome not in salas:
                salas[sala_nome] = SalaDeJogo(sala_nome) # Se a sala não existir, cria uma nova sala
            sala = salas[sala_nome]

        jogador_id = sala.adicionar_jogador(client_socket)
        
        # Se a sala estiver cheia, informar o cliente e encerrar a conexão
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

        client_socket.sendall(f"Jogo iniciado!\n{formatar_tabuleiro(sala.tabuleiro.unicode())}\n".encode())
        client_socket.sendall("Sua vez!\n".encode() if jogador_id == sala.turno else "Aguarde o adversário...\n".encode())

        # Loop principal do jogo
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
        # Encerrar a conexão com o cliente e notificar o adversário
        for jogador in sala.jogadores:
            if jogador != client_socket:
                jogador.sendall("O adversário desconectou. O jogo foi encerrado.\n".encode())
           
        sala.remover_jogador(client_socket)
        client_socket.close()     
        logging.info(f"Conexão com jogador encerrada na sala '{sala_nome}'.")
        
        # Se a sala estiver vazia, removê-la
        if len(sala.jogadores) == 0:
            with salas_lock:
                if sala_nome in salas:
                    del salas[sala_nome]
                    logging.info(f"Sala '{sala_nome}' removida após o término da partida.")


def start_server():
    """
    Inicia o servidor de xadrez e aguarda conexões de clientes.
    O servidor é configurado para reutilizar o endereço e porta, e começa a escutar por conexões
    de clientes. Para cada nova conexão aceita, uma nova thread é iniciada para lidar com o cliente.
    O servidor pode ser interrompido com um KeyboardInterrupt (Ctrl+C), momento em que todas as conexões
    de clientes são fechadas e o servidor é encerrado de forma limpa.
    Variáveis Globais:
    - running (bool): Indica se o servidor deve continuar rodando.
    Exceções:
    - KeyboardInterrupt: Capturada para permitir o encerramento gracioso do servidor.
    Recursos Limpos:
    - Todas as conexões de clientes são fechadas.
    - O socket do servidor é fechado.
    Logs:
    - Informações sobre o início e encerramento do servidor.
    - Informações sobre novas conexões aceitas.
    - Erros ao fechar conexões de clientes.
    - Informações sobre salas removidas.
    """
    
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
