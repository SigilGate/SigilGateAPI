import argparse
import os


def main() -> None:
    parser = argparse.ArgumentParser(prog="sigilgateapp")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="запустить HTTP API сервер")
    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn
        host = os.environ.get("SIGILGATEAPP_HOST", "127.0.0.1")
        port = int(os.environ.get("SIGILGATEAPP_PORT", "8000"))
        uvicorn.run("sigilgateapp.api.app:app", host=host, port=port)
    else:
        parser.print_help()
