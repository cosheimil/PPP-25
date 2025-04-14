import os
import json
import xml.etree.ElementTree as ET
import platform
import signal
import psutil
from utils.config import Config

class ProcessUtils:
    @staticmethod
    def collect_process_info():
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status']):
            try:
                info = proc.info
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    @staticmethod
    def save_info_to_file(data: list, filename: str, format_type: str = "json"):
        """
        Сохраняет список процессов в файл в формате JSON или XML.
        """
        if format_type == "json":
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        elif format_type == "xml":
            root = ET.Element("processes")
            for proc in data:
                proc_elem = ET.SubElement(root, "process")
                for key, value in proc.items():
                    child = ET.SubElement(proc_elem, key)
                    child.text = str(value)
            tree = ET.ElementTree(root)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    @staticmethod
    def get_available_signals():
        """
        Возвращает список доступных сигналов для текущей ОС.
        """
        signals = {}
        for sig in ["SIGTERM", "SIGKILL", "SIGINT"]:
            if hasattr(signal, sig):
                signals[sig] = getattr(signal, sig)
        return signals

    @staticmethod
    def send_signal(pid: int, sig: str) -> str:
        sig = sig.upper()
        signals = ProcessUtils.get_available_signals()
        if sig not in signals:
            return f"Сигнал {sig} не поддерживается в этой системе."

        try:
            os.kill(pid, signals[sig])
            return f"Сигнал {sig} отправлен процессу с PID {pid}"
        except Exception as e:
            return f"Ошибка при отправке сигнала: {e}"
