import sys
from server import Server
from client import Client

def run_server():
    server = Server()
    server.start()

def run_client():
    client = Client()
    try:
        while True:
            command = input("Введите команду (UPDATE | SIGNAL <pid> <SIGTERM/SIGKILL> | EXIT): ").strip()
            if command.upper() == "EXIT":
                break
            client.send_command(command)
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("server", "client"):
        print("Использование: python main.py [server|client]")
        sys.exit(1)

    if sys.argv[1] == "server":
        run_server()
    else:
        run_client()
