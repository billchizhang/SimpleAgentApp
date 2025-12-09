import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, Any, Optional

import requests

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from function_call.generic_call import ApiToolCall, call_api
except ModuleNotFoundError:
    raise SystemExit(
        "Unable to import function_call.generic_call. "
        "Please run this script from within the repository root or ensure the project is on PYTHONPATH."
    )


DATA_DIR = Path(__file__).parent / "data"
SERVER_READY_TIMEOUT = 15
SERVER_POLL_INTERVAL = 0.5
SERVER_LOG_PATH = Path(__file__).with_name("api_server.log")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000


def load_tool_call(filename: str) -> ApiToolCall:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as f:
        payload = json.load(f)
    return ApiToolCall(**payload)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Integration test harness for generic_call.")
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host where the FastAPI service should listen (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port where the FastAPI service should listen (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--use-external-server",
        action="store_true",
        help="Skip starting uvicorn and assume the API service is already running.",
    )
    return parser.parse_args()


def start_api_server(host: str, port: int) -> tuple[subprocess.Popen, Any]:
    """Boot the FastAPI server in the background for the duration of the tests."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "tool_api.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    log_file = SERVER_LOG_PATH.open("w")
    process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT)
    try:
        _wait_for_server_ready(host, port, process)
    except Exception:
        stop_api_server(process, log_file, force=True)
        raise
    return process, log_file


def _wait_for_server_ready(host: str, port: int, process: Optional[subprocess.Popen]) -> None:
    deadline = time.time() + SERVER_READY_TIMEOUT
    health_url = f"http://{host}:{port}/docs"
    while time.time() < deadline:
        if process is not None and process.poll() is not None:
            raise RuntimeError(f"API server exited early. Inspect {SERVER_LOG_PATH} for details.")
        try:
            response = requests.get(health_url, timeout=0.5)
            if response.status_code < 500:
                return
        except requests.RequestException:
            time.sleep(SERVER_POLL_INTERVAL)
    raise RuntimeError(
        f"API server failed to start within {SERVER_READY_TIMEOUT} seconds. "
        f"Inspect {SERVER_LOG_PATH} for details."
    )


def stop_api_server(process: subprocess.Popen, log_file, force: bool = False) -> None:
    if process and process.poll() is None:
        if force:
            process.kill()
        else:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
    if log_file is not None:
        log_file.close()


def assert_uppercase(response: Dict[str, Any], call: ApiToolCall) -> None:
    expected = call.params["text"].upper()
    if response.get("text") != expected:
        raise AssertionError(f"Uppercase endpoint returned {response}, expected text={expected}")


def assert_weather(response: Dict[str, Any], call: ApiToolCall) -> None:
    required_keys = {"date", "city", "temperature_c"}
    missing = required_keys.difference(response.keys())
    if missing:
        raise AssertionError(f"Weather endpoint missing keys: {missing} in response {response}")
    if response["city"] != call.params["city"]:
        raise AssertionError(f"City mismatch: {response['city']} != {call.params['city']}")
    if response["date"] != call.params["date"]:
        raise AssertionError(f"Date mismatch: {response['date']} != {call.params['date']}")


def assert_count_word(response: Dict[str, Any], call: ApiToolCall) -> None:
    expected = len(call.params["text"].split())
    if response.get("word_count") != expected:
        raise AssertionError(f"Count_word endpoint returned {response}, expected word_count={expected}")


def run_test_case(filename: str, validator: Callable[[Dict[str, Any], ApiToolCall], None]) -> None:
    tool_call = load_tool_call(filename)
    response = call_api(tool_call)
    if "error" in response:
        raise AssertionError(f"{filename} produced API error: {response['error']}")
    validator(response, tool_call)
    print(f"{filename} passed with response: {response}")


def main() -> None:
    args = parse_args()

    server_proc = None
    log_file = None

    if args.use_external_server:
        print(f"Checking availability of existing API server at http://{args.host}:{args.port} ...")
        _wait_for_server_ready(args.host, args.port, process=None)
    else:
        try:
            server_proc, log_file = start_api_server(args.host, args.port)
        except RuntimeError as exc:
            raise SystemExit(
                f"{exc}\n"
                f"If you need to run against a manually managed server, start uvicorn separately "
                f"(e.g. `uvicorn tool_api.main:app --host {args.host} --port {args.port}`) "
                f"and rerun this script with --use-external-server."
            )

    try:
        run_test_case("uppercase_call.json", assert_uppercase)
        run_test_case("weather_call.json", assert_weather)
        run_test_case("count_word_call.json", assert_count_word)
        print("All generic_call integration tests passed.")
    finally:
        if server_proc is not None:
            stop_api_server(server_proc, log_file)


if __name__ == "__main__":
    main()
