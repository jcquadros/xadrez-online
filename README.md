# Nome do Projeto
Servidor de Jogo de Xadrez Multiplayer

## Descrição
Este projeto consiste em um servidor de jogo de xadrez multiplayer que permite a dois jogadores se conectarem e jogarem xadrez em tempo real. O servidor gerencia as salas de jogo, valida os movimentos dos jogadores e notifica os jogadores sobre o estado do jogo, incluindo xeque, xeque-mate e empates. O cliente se conecta ao servidor e permite que o jogador envie movimentos e receba atualizações do jogo.

## Tecnologias Utilizadas
- Linguagem de programação: Python

- Bibliotecas/Frameworks:

    - socket: Para comunicação em rede entre cliente e servidor.

    - threading: Para lidar com múltiplos clientes simultaneamente.

    - chess: Para gerenciar as regras e o estado do jogo de xadrez.

    - logging: Para registrar eventos e erros no servidor.

## Como Executar
Requitos: Python 3 instalado.

1. Clone o repositório:
```sh
git clone https://github.com/jcquadros/xadrez-online.git
```
2. Navegue até o diretório do projeto:
```sh
cd xadrez-online
```
3. Instale as dependências:
```sh
pip install -r requirements.txt
```
4. Execute o servidor:
```sh
python servidor.py
```
5. Execute o cliente (em um terminal separado):
```sh
python cliente.py
```
## Conecte-se ao servidor:

Quando o cliente for iniciado, ele se conectará automaticamente ao servidor.

O servidor solicitará o nome da sala para entrar. Digite um nome de sala e pressione Enter.

Aguarde outro jogador se conectar à mesma sala para iniciar o jogo.

## Como Testar
1. Teste de Conexão:

    - Execute o servidor e dois clientes.

    - Conecte ambos os clientes à mesma sala e verifique se o jogo inicia corretamente.

2. Teste de Movimentos:

    - Realize movimentos válidos e inválidos para verificar se o servidor valida corretamente os movimentos.

    - Verifique se o servidor notifica os jogadores sobre xeque, xeque-mate e empates.

    - O jogo espera que os comandos de movimento estejam no formato: **MOV:e2e4** . Que são as coordenadas de um tabuleiro de xadrez. 
    - Sujestão de sequência de movimentos que levam a um xeque: 
        - J1-> `MOV:e2e4` (peão avança)
        - J2-> `MOV:f7f5` (peão avança)
        - J1-> `MOV:e4e5` (peão elimina peao)
        - J2-> `MOV:g7g5` (peão avança)
        - J1-> `MOV:d1h5` (rainha avança - xeque-mate!)
    
3. Teste de Desconexão:

    - Desconecte um dos clientes durante o jogo e verifique se o servidor encerra a partida corretamente e notifica o outro jogador.

## Limites do Servidor

O servidor foi testado com diferentes números de clientes para avaliar seu consumo de memória e estabilidade. Abaixo estão os resultados:

| Número de Clientes |	Uso de Memória (MB)	| Observações |
| -------------------| ---------------------| ------------|
| 0 |	15.4 MB	| Servidor ocioso (sem clientes). |
| 1 |	15.4 MB	| Um cliente conectado. |
| 10 |	17.4 MB	| Dez clientes conectados. |
| 50 | 	29.8 MB	| Cinquenta clientes conectados. |
| 100 | 	44.0 MB	| Cem clientes conectados. |

### Conclusões:
1. Crescimento Linear:

    O consumo de memória aumenta linearmente com o número de clientes. Cada cliente adicional consome aproximadamente 0.3 MB de memória.

2. Limite de Cem Clientes:

    Com 100 clientes, o servidor consumiu 44.0 MB de memória. No entanto, ao tentar interromper o servidor com Ctrl+C, ele não respondeu corretamente, exigindo o uso de kill para encerrá-lo. Isso indica que o servidor pode ter problemas para lidar com um grande número de conexões simultâneas.

3. Estabilidade:

    O servidor funcionou corretamente com até 50 clientes, mas apresentou instabilidade com 100 clientes, especialmente durante o encerramento. Isso sugere que o servidor precisa de melhorias no gerenciamento de conexões e no tratamento de sinais de interrupção.

4. Recomendações:

    Otimização de Memória: Reduzir o consumo de memória por cliente pode permitir que o servidor suporte mais conexões.

    Melhor Tratamento de Sinais: Implementar um tratamento adequado para sinais como SIGINT (Ctrl+C) pode melhorar a estabilidade do servidor.

    Limite de Conexões: Definir um limite máximo de clientes pode evitar sobrecarga do servidor.

    Usar selects para não precisar criar um monte de thread. Um único processo gerenciando várias conexões diminuindo o overhead de criaçao e gerenciamento de threads além de reduzir o consumo de memória. 