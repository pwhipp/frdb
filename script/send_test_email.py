#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from frdb import send_email


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a test email using the FRDB mail configuration.")
    parser.add_argument("to_address", help="Email address to receive the test message")
    args = parser.parse_args()

    send_email(
        args.to_address,
        "FRDB email test",
        "This is a test email from the FRDB mail configuration.",
    )
    print(f"Sent FRDB test email to {args.to_address}")


if __name__ == "__main__":
    main()
