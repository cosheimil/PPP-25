from typing import Dict, List, Optional, Any, NoReturn
import asyncio
import json
import argparse
import getpass
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException
from colorama import Fore, Style, init as colorama_init
import logging
from celery import Celery
from celery.result import AsyncResult

# Initialize colorama and logging
colorama_init()
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Constants
API_URL = "http://localhost:8000"
REDIS_URL = "redis://localhost:6379/0"

@dataclass
class TaskConfig:
    word: str
    algorithm: str
    corpus_id: int

class CeleryClient:
    def __init__(self):
        self.app = Celery(
            "tasks",
            broker=REDIS_URL,
            backend=REDIS_URL
        )

    def send_task(self, task: TaskConfig) -> str:
        task_obj = self.app.send_task(
            "fuzzy_search_task",
            args=[task.word, task.algorithm, task.corpus_id]
        )
        return task_obj.id

    def get_result(self, task_id: str) -> AsyncResult:
        return self.app.AsyncResult(task_id)

class APIClient:
    @staticmethod
    def get_token(email: str, password: str) -> str:
        try:
            response = requests.post(
                f"{API_URL}/auth/login/",
                json={"email": email, "password": password}
            )
            response.raise_for_status()
            return response.json()["token"]
        except RequestException as e:
            raise Exception(f"Authentication failed: {str(e)}")

class OutputFormatter:
    @staticmethod
    def format_json(obj: Any) -> str:
        return json.dumps(obj, indent=2, ensure_ascii=False)

    @staticmethod
    def color_block(label: str, color: str) -> str:
        return f"{color}{label}{Style.RESET_ALL}"

class TaskManager:
    def __init__(self):
        self.celery_client = CeleryClient()

    async def poll_status(self, task_id: str) -> None:
        while True:
            result = self.celery_client.get_result(task_id)
            
            if result.successful():
                self._handle_success(task_id, result.result)
                break
            elif result.state == "PROGRESS":
                self._handle_progress(result.info)
            elif result.failed():
                print(OutputFormatter.color_block("[FAILED]", Fore.RED))
                print(f"Task failed: {result.result}")
                break
            else:
                print(OutputFormatter.color_block("[STATUS]", Fore.YELLOW), result.state)
            
            await asyncio.sleep(1)

    def _handle_success(self, task_id: str, res: Optional[Dict]) -> None:
        if not res or res.get("results") is None or res.get("execution_time") is None:
            print(OutputFormatter.color_block("[FAILED]", Fore.RED))
            print(f"Task ID: {task_id}")
            print("Task completed but result is missing. Possible invalid corpus_id.")
        elif "error" in res:
            print(OutputFormatter.color_block("[ERROR]", Fore.RED))
            print(f"Task ID: {task_id}")
            print(f"Error: {res['error']}")
        else:
            print(OutputFormatter.color_block("[COMPLETED]", Fore.GREEN))
            print(OutputFormatter.format_json({
                "task_id": task_id,
                "execution_time": res["execution_time"],
                "results": res["results"]
            }))
        print("-" * 50)

    def _handle_progress(self, meta: Optional[Dict]) -> None:
        meta = meta or {}
        progress = meta.get('progress', 0)
        current_word = meta.get('current_word', '?')
        print(OutputFormatter.color_block("[PROGRESS]", Fore.BLUE), 
              f"{progress}% — {current_word}")

class CLI:
    def __init__(self):
        self.task_manager = TaskManager()
        self.celery_client = CeleryClient()

    async def run_interactive_session(self, token: str) -> None:
        print("\nAvailable commands: search, status, exit\n")
        while True:
            action = input("> ").strip().lower()
            if action == "exit":
                break
            elif action == "search":
                await self._handle_search()
            elif action == "status":
                await self._handle_status()
            else:
                print(OutputFormatter.color_block("Unknown command.", Fore.YELLOW))

    async def _handle_search(self) -> None:
        try:
            word = input("Word to search: ").strip()
            algorithm = input("Algorithm (levenshtein/ngram): ").strip()
            corpus_id = int(input("Corpus ID: ").strip())
            
            task = TaskConfig(word=word, algorithm=algorithm, corpus_id=corpus_id)
            task_id = self.celery_client.send_task(task)
            
            print(OutputFormatter.color_block("[TASK QUEUED]", Fore.CYAN),
                  f"Task ID: {task_id}")
            print("Use `status` command to check result.\n")
        except ValueError:
            print(OutputFormatter.color_block(
                "Corpus ID must be an integer.", Fore.RED))

    async def _handle_status(self) -> None:
        task_id = input("Enter Task ID: ").strip()
        await self.task_manager.poll_status(task_id)

    @staticmethod
    def parse_file(file_path: str) -> List[Dict]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [json.loads(line.strip()) 
                        for line in f if line.strip()]
        except (IOError, json.JSONDecodeError) as e:
            logger.error(f"Error reading tasks file: {e}")
            return []

    async def run_task_sequence(self, tasks: List[Dict]) -> None:
        for task_data in tasks:
            try:
                task = TaskConfig(**task_data)
                task_id = self.celery_client.send_task(task)
                print(OutputFormatter.color_block("[TASK STARTED]", Fore.CYAN),
                      f"Task ID: {task_id}")
                await self.task_manager.poll_status(task_id)
            except Exception as e:
                logger.error(f"Error processing task: {e}")

def main() -> NoReturn:
    parser = argparse.ArgumentParser(
        description="CLI Client for Fuzzy Search (Celery-based)")
    parser.add_argument("--script", help="Path to .jsonl file with search tasks")
    args = parser.parse_args()

    print("Enter your credentials to authenticate:")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    try:
        token = APIClient.get_token(email, password)
        print(OutputFormatter.color_block(
            "Authenticated successfully.", Fore.GREEN))
        
        cli = CLI()
        if args.script:
            tasks = cli.parse_file(args.script)
            asyncio.run(cli.run_task_sequence(tasks))
        else:
            print(OutputFormatter.color_block(
                "\nNo script provided. Entering interactive mode.",
                Fore.CYAN))
            asyncio.run(cli.run_interactive_session(token))
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
