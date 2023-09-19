import socket
import os
import threading
import argparse
import time



# Sincroniza acesso ao arquivo de log
log_lock = threading.Lock()

#Quando um cliente se conecta ao servidor, 
# o servidor cria uma nova thread para lidar com esse cliente em handle_client().
# client_socket = conexao entre o cliente e servidor
def handle_client(client_socket, base_dir):
    try:
        # timeout de 20 segundos
        client_socket.settimeout(20)  

        # Receber os dados da requisição
        request_data = client_socket.recv(1024)
        if not request_data:
            return

        # Decodificar os bytes recebidos para uma string
        # recv é usado para receber dados da conexão do cliente.
        # Ele aceita um argumento que especifica o número máximo de bytes
        # a serem lidos de uma vez.
        # No caso dessa linha, no máximo 1024 bytes de dados do cliente estao sendo lidos
        # de uma só vez.
        # request_text armazena todas as informacoes da requisicao GET /index.html HTTP/1.1, host, ...
        request_text = request_data.decode('utf-8')

        #Caso a requisição não seja GET, retornar um erro 502 Not Implemented
        if not request_text.startswith('GET'):
            response = "HTTP/1.1 502 Not Implemented\r\n\r\nMethod Not Implemented"
            client_socket.send(response.encode())
            # Registrar informações de log
            log_request(client_socket, request_text, 502,log_file='log.txt')
            return

        #Caso contrario, seguir com a tratativa do GET
        try:
            # Obter o caminho do arquivo a ser servido
            path = request_text.split(' ')[1]
        except IndexError:
            response = "HTTP/1.1 400 Bad Request\r\n\r\nBad Request"
            client_socket.send(response.encode())
             # Registrar informações de log
            log_request(client_socket, request_text,400, log_file='log.txt')
            return

        # Se o caminho terminar com '/', servir o arquivo passado de dentro da pasta
        file_path = os.path.join(base_dir, path.lstrip('/'))
       
        cwd = os.getcwd()
        
        caminho = cwd + file_path
     

        if not os.path.exists(caminho) or not os.path.isfile(caminho):
            #cria uma sequência de bytes vazia
            not_found_content = b""
            #obtem o caminho do arquivo NotFound.html
            not_found_file_path = cwd + base_dir +'\\NotFound.html'
            if os.path.exists(not_found_file_path):
                with open(not_found_file_path, 'rb') as not_found_file:
                    not_found_content = not_found_file.read()
            # Formata a resposta desejada como 400
            response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {len(not_found_content)}\r\n\r\n"
            # Enviar a resposta com o conteúdo de NotFound.html pelo socket
            client_socket.send(response.encode() + not_found_content)
             # Registrar informações de log
            log_request(client_socket, request_text, 404,log_file='log.txt')
            return

        with open(caminho, 'rb') as file:
            content = file.read()
            # Formata a resposta desejada como 200
            response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\n\r\n"
            # Enviar a resposta com o conteúdo do arquivo pelo socket
            client_socket.send(response.encode() + content)
             # Registrar informações de log
            log_request(client_socket, request_text,200, log_file='log.txt')

    # Tratar o timeout de 20 segundos
    except socket.timeout:
        print("Timeout de 20 segundos ocorreu. Encerrando a conexão.")
        # Fechar o socket do cliente se houver timeout
        client_socket.close()

    finally:
        client_socket.close()

def log_request(client_socket, request_text, status, log_file):
    # Obter o timestamp atual
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    # Obter o endereço IP do cliente (que é o destino que o socket está se comunicando)
    client_ip = client_socket.getpeername()[0]
    
    request = request_text.split('\n')[0]
    # Formatar a entrada de log
    log_entry = f"{timestamp} - {client_ip} - [{status}] -{request}"

    # Bloquear o acesso ao arquivo de log para evitar problemas de requisicoes ao mesmo tempo
    with log_lock:
        # Escrever a entrada de log no arquivo de log -> 'a' signidica que será escrito no arquivo
        with open(log_file, 'a') as log:
            log.write(log_entry + '\n')

def main():
    # Parsear os argumentos da linha de comando
    parser = argparse.ArgumentParser()
    # Argumento obrigatório: pasta/diretório base dos arquivos a serem servidos
    parser.add_argument('base_dir')
    # Argumento opcional: porta TCP onde o servidor vai ouvir (padrão: 8080)
    args = parser.parse_args()

    # Criar um socket TCP/IP
    #AF_INET = familia de enderecos IPv4
    #SOCK_STREAM = socket de fluxo TCP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Impedir o erro "Address already in use"
    server_socket.bind(('127.0.0.1', 8080))
    # Ouvir por até 1 conexões simultâneas
    server_socket.listen(1)

    print(f"Servidor HTTP está ouvindo na porta 8080, servindo arquivos de {args.base_dir}")

    while True:
        # Aguardar por novas conexões
        #client_socket = socket do cliente
        #client_address = endereço do cliente
        client_socket, client_address = server_socket.accept()
        print(f"Conexão de {client_address}")

        # Crie uma thread para lidar com o cliente e continue ouvindo por novas conexões
        # handle_client = chamada de uma nova thread
        # args = argumentos passados para a thread (client_socket = socket do cliente, args.base_dir = pasta base dos arquivos a serem servidos)
        client_handler = threading.Thread(target=handle_client, args=(client_socket, args.base_dir))
        client_handler.start()

if __name__ == "__main__":
    main()
