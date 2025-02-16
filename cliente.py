import socket
import threading

def receber_mensagens(client_socket):
    """Função para receber e exibir mensagens do servidor."""
    while True:
        try:
            mensagem = client_socket.recv(1024).decode()
            if not mensagem:
                print("Conexão encerrada pelo servidor.")
                break
            print(mensagem)
        except Exception as e:
            print(f"Erro ao receber mensagem: {e}")
            break

def main():
    HOST = "127.0.0.1"  # IP do servidor
    PORT = 65432         # Porta do servidor

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")
        return

    threading.Thread(target=receber_mensagens, args=(client_socket,), daemon=True).start()

    try:
        while True:
            mensagem = input()
            if not mensagem.strip():
                print("Entrada vazia. Digite um comando válido.")
                continue
            if mensagem.lower() == "sair":
                print("Encerrando conexão...")
                break
            if "xeque-mate!" in mensagem.lower() or "empate" in mensagem.lower() or "encerrado" in mensagem.lower():
                print("O jogo terminou. Desconectando...")
                break  # Se o jogo acabou, encerra a conexão
            client_socket.sendall(mensagem.encode())
    except KeyboardInterrupt:
        print("\nEncerrando conexão...")
    except Exception as e:
        print(f"Erro inesperado: {e}")
    finally:
        print("Conexão encerrada.")
        client_socket.close()

if __name__ == "__main__":
    main()
