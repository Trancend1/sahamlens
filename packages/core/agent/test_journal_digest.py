"""Journal digest boundary: structural counts only, never leaks text or rupiah."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb
from packages.core.agent.journal_digest import journal_digest
from packages.core.journal.models import TradePlan
from packages.core.journal.repo import create_plan
from scripts.migrate import applied_versions, apply_migration, discover_migrations

# Distinctive sentinels that must never reach the digest payload.
SENTINEL_THESIS = "PRIVATETHESISALPHA"
SENTINEL_ENTRY = "PRIVATEENTRYBETA"
SENTINEL_TARGET = "PRIVATETARGETGAMMA"
SENTINEL_INVALIDATION = "PRIVATEINVALIDATIONDELTA"
POSITION_SIZE = 123456789
MAX_LOSS = 87654321


def _migrated_db(tmp_path: Path) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(str(tmp_path / "test.duckdb"))
    applied_versions(conn)
    for path in discover_migrations():
        apply_migration(conn, path)
    return conn


def _plan(plan_id: int, symbol: str, *, emotion: str | None, invalidation: str) -> TradePlan:
    return TradePlan(
        id=plan_id,
        symbol=symbol,
        setup_type="breakout",
        thesis=SENTINEL_THESIS,
        entry_plan=SENTINEL_ENTRY,
        stop_level=9000.0,
        invalidation=invalidation,
        target=SENTINEL_TARGET,
        position_size_rupiah=POSITION_SIZE,
        max_loss_rupiah=MAX_LOSS,
        # test helper passes str|None; TradePlan.emotion is the EmotionLevel literal.
        emotion=emotion,  # type: ignore[arg-type]
        created_at=datetime.now(UTC),
    )


def test_empty_journal_returns_zeroed_digest(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        digest = journal_digest(conn)
    assert digest.entry_count == 0
    assert digest.by_status == {}
    assert digest.missing_invalidation_count == 0


def test_digest_counts_status_setup_emotion_and_gaps(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        create_plan(conn, _plan(1, "BBCA", emotion="fearful", invalidation="below 9000"))
        create_plan(conn, _plan(2, "BBRI", emotion=None, invalidation="   "))
        digest = journal_digest(conn)

    assert digest.entry_count == 2
    assert digest.by_status == {"planned": 2}
    assert digest.by_setup == {"breakout": 2}
    assert digest.by_emotion == {"fearful": 1, "unspecified": 1}
    assert digest.missing_invalidation_count == 1
    assert digest.missing_emotion_count == 1


def test_digest_never_leaks_free_text_or_rupiah(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        create_plan(conn, _plan(1, "BBCA", emotion="fearful", invalidation=SENTINEL_INVALIDATION))
        digest = journal_digest(conn)

    payload = json.dumps(digest.model_dump(), ensure_ascii=False)
    for sentinel in (SENTINEL_THESIS, SENTINEL_ENTRY, SENTINEL_TARGET, SENTINEL_INVALIDATION):
        assert sentinel not in payload
    assert str(POSITION_SIZE) not in payload
    assert str(MAX_LOSS) not in payload


def test_digest_scopes_to_symbol(tmp_path: Path) -> None:
    with _migrated_db(tmp_path) as conn:
        create_plan(conn, _plan(1, "BBCA", emotion="calm", invalidation="x"))
        create_plan(conn, _plan(2, "BBRI", emotion="calm", invalidation="y"))
        digest = journal_digest(conn, symbol="BBCA")
    assert digest.entry_count == 1
