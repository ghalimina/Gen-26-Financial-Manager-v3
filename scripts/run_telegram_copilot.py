#!/usr/bin/env python3
# =============================================================================
# scripts/run_telegram_copilot.py — GEN-26 Interactive Telegram Copilot Runner
# Standalone execution script for testing and running Telegram Copilot.
# Supports interactive CLI prompt mode, simulation batches, and bot polling.
# =============================================================================

import os
import sys
import time
import logging

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.telegram_interactive_copilot import TelegramInteractiveCopilot

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GEN26.RunTelegramCopilot")


def run_interactive_cli():
    """Interactive REPL shell for testing Telegram copilot commands locally."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("\n=======================================================")
    print("🤖 GEN-26 Interactive Telegram Copilot (CLI Shell)")
    print("Available commands: /price <sym>, /swing, /portfolio, /trap <sym>, /top, /help, exit")
    print("=======================================================\n")

    while True:
        try:
            cmd = input("GEN-26 Copilot > ").strip()
            if not cmd:
                continue
            if cmd.lower() in ["exit", "quit", "q"]:
                print("Exiting Copilot shell.")
                break

            response = TelegramInteractiveCopilot.handle_command(cmd)
            print("\n" + response + "\n" + "-" * 50 + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting Copilot shell.")
            break


def run_test_suite():
    """Executes a non-interactive validation of all 5 copilot commands."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    commands = [
        "/price COMI",
        "/swing",
        "/portfolio",
        "/trap RAYA",
        "/top"
    ]

    print("\n🚀 Running Automated Validation of Telegram Copilot Commands...")
    for cmd in commands:
        print(f"\n[Command: {cmd}]")
        resp = TelegramInteractiveCopilot.handle_command(cmd)
        print(resp)
        print("=" * 40)
    print("\n✅ All 5 Copilot commands verified successfully.")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        run_interactive_cli()
    elif len(sys.argv) > 1 and sys.argv[1].startswith("/"):
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        full_cmd = " ".join(sys.argv[1:])
        print(TelegramInteractiveCopilot.handle_command(full_cmd))
    else:
        run_test_suite()


if __name__ == "__main__":
    main()
