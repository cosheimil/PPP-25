import socket
import threading
import json
from utils.process_utils import ProcessUtils
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger("Server")

class ClientHandler(threading.Thread):
    """
    Класс-обработчик для каждого клиента. Запускается в отдельном потоке.
    """
    def __init__(self, conn, addr):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        logger.info(f"Клиент {addr} подключился")

    def run(self):
        try:
            while True:
                data = self.conn.recv(1024).decode()
                if not data:
                    logger.info(f"Клиент {self.addr} отключился")
                    break

                logger.info(f"Получена команда от {self.addr}: {data}")
                command_parts = data.strip().split()

                if command_parts[0] == "UPDATE":
                    self.handle_update()
                elif command_parts[0] == "SIGNAL" and len(command_parts) == 3:
                    self.handle_signal(int(command_parts[1]), command_parts[2])
                else:
                    self.conn.sendall("Неверная команда\n".encode())

        except Exception as e:
            logger.error(f"Ошибка клиента {self.addr}: {e}")
        finally:
            self.conn.close()

    def handle_update(self, format_type="JSON"):
        data = ProcessUtils.collect_process_info()

        # Сохраняем оба формата
        json_file = "server_output.json"
        xml_file = "server_output.xml"
        ProcessUtils.save_info_to_file(data, json_file, "json")
        ProcessUtils.save_info_to_file(data, xml_file, "xml")

        # Отправляем оба файла клиенту
        for file_path in [json_file, xml_file]:
            try:
                with open(file_path, "rb") as f:
                    file_data = f.read()
                    self.conn.sendall(len(file_data).to_bytes(4, 'big'))
                    self.conn.sendall(file_data)
                    logger.info(f"Отправлен файл: {file_path}")
            except Exception as e:
                logger.error(f"Ошибка отправки файла {file_path}: {e}")

    def handle_signal(self, pid: int, signal_name: str):
        """
        Отправка сигнала процессу.
        """
        result = ProcessUtils.send_signal(pid, signal_name)
        self.conn.sendall(result.encode())
        logger.info(f"{result} -> {self.addr}")


class Server:
    """
    Главный серверный класс.
    """
    def __init__(self):
        self.host = Config.HOST
        self.port = Config.PORT
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        logger.info(f"Сервер запущен на {self.host}:{self.port}")

    def start(self):
        """
        Запускаем основной цикл ожидания клиентов.
        """
        try:
            while True:
                conn, addr = self.sock.accept()
                handler = ClientHandler(conn, addr)
                handler.start()
        except KeyboardInterrupt:
            logger.info("Сервер остановлен вручную")
        finally:
            self.sock.close()
