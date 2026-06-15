"""Hermes runtime entrypoint (M4.7). Run with `uv run python -m services.hermes`."""

from __future__ import annotations

import argparse
import logging
import os
import sys

from packages.core.ai.router import CircuitBreaker, CostBudget, ModelRouter, load_budget
from packages.core.schemas.repository import open_connection

from services.hermes.config import TELEGRAM_CHAT_ID_ENV, TELEGRAM_TOKEN_ENV, load_config
from services.hermes.telegram_listener import TelegramListener

logger = logging.getLogger(__name__)


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m services.hermes",
        description="Hermes — SahamLens agentic research runtime (long-polling Telegram listener).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _parse_args(argv)
    _setup_logging()

    config, provider = load_config()

    print(config.status_text())
    if not config.enabled:
        return 0

    logger.info(
        "Hermes session %s starting | provider=%s telegram=%s",
        config.session_id[:12],
        config.provider_name,
        "yes" if config.telegram_configured else "no",
    )

    token = os.environ.get(TELEGRAM_TOKEN_ENV, "").strip()
    chat_id = os.environ.get(TELEGRAM_CHAT_ID_ENV, "").strip()

    if not token or not chat_id:
        print(
            "Telegram token/chat ID tidak ditemukan. Set SAHAMLENS_TELEGRAM_BOT_TOKEN dan SAHAMLENS_TELEGRAM_CHAT_ID."
        )
        return 1

    conn = open_connection()
    budget: CostBudget = load_budget()
    router = ModelRouter()
    breaker = CircuitBreaker(budget)
    listener = TelegramListener(
        conn=conn,
        provider=provider,
        router=router,
        breaker=breaker,
        session_id=config.session_id,
        telegram_token=token,
        telegram_chat_id=chat_id,
    )

    try:
        listener.start()
    except KeyboardInterrupt:
        print("\nReceived interrupt, shutting down...")
        listener.stop()

    logger.info("Hermes session %s finished", config.session_id[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
