### Critic / Devil's Advocate Review

1. ai_log_id via MAX(id) diff — fragile
Masalah: _handle_brief dan _handle_ticker_snapshot hitung ai_log_id via SELECT MAX(id) FROM ai_log sebelum/sesudah LLM call. Jika proses lain nulis ke ai_log di antara, linkage-nya salah.
Risiko: Rendah — single-process single-user. DuckDB juga single-writer.
Rekomendasi: Terima utk V2. Jika multi-process nanti, migrasi ke RETURNING id dari log_ai_call().
2. Journal draft bypass symbol='DRAFT'
Masalah: writes.py _apply_action untuk save_journal_draft insert langsung ke journal dgn symbol='DRAFT' (bypass TradePlan normalizer karena normalize_ticker('DRAFT') gagal). Row ini muncul di aggregate digest sebagai planned entry.
Risiko: Rendah-sedang. journal_digest_tool hanya aggregate — symbol DRAFT terlihat di count tapi tidak leak thesis/rupiah. Tidak mengganggu fitur existing.
Rekomendasi: Terima utk V2. Jika perlu filter nanti, tambah kolom is_draft di migrasi terpisah.
3. Telegram listener error handling
Masalah: _handle_update tidak punya try/except individual. Jika 1 update raise exception, offset tidak ter-update dan update itu akan reprocess di polling berikutnya.
Risiko: Rendah. Polling loop start() sudah catch Exception dan lanjut. Kasus terburuk: 1 pesan diproses 2x (idempoten di sisi dispatch — write action pakai idempotency_key, read-only tidak masalah).
Rekomendasi: Terima utk V2. Tambah try/except di _handle_update jika jadi masalah.
4. Missing Discord adapter (M5 deferred)
Masalah: Telegram listener punya kode surface-specific (_handle_update membaca message.chat.id dari Telegram JSON). M5 harus refactor untuk reuse pipeline.
Risiko: Sedang. Pipeline (parse_intent → check_intent_allowed → dispatch_intent → check_outbound_text) sudah clean terpisah di modul sendiri. M5 cukup buat adapter baru yang panggil pipeline yang sama — tidak perlu refactor besar.
Rekomendasi: Terima. Pipeline granularity sudah benar.
5. Test coverage entrypoint
Masalah: __main__.py tidak punya test. Hanya --help dan disabled-by-default yang diverifikasi manual.
Risiko: Rendah. Entrypoint tipis (~45 lines logika, mostly wiring).
Rekomendasi: Tambah test di PR berikutnya jika mau. Tidak blocking.
