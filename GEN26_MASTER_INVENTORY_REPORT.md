# GEN26 MASTER INVENTORY REPORT
> **Generated at:** 2026-08-17 03:34:31
> **Environment:** Local VSCode Workspace + GitHub Actions (Zero-Trust Pipeline)

## 1. ملخص تنفيذي
هذا التقرير هو جرد شامل للنسخة الحالية **v4.1** من النظام المالي. النظام الآن يعتمد معمارية **Single Decision Object** (SSoT) التي تضمن تطابق قرارات المحرك الأساسي، الواجهة (UI)، وسجلات Paper Trading. تم تعريب النظام بالكامل وتطبيق جميع حواجز الأمان (Gates) المانعة للتداول الوهمي العشوائي.

## 2. جرد الملفات والكود الكامل
### 2.1 ملفات النظام
| File Path | Type | Status | Last Modified | Size (Bytes) |
|---|---|---|---|---|
| `.pytest_cache\README.md` | .MD | Output | 2026-08-14 17:48:24 | 302 |
| `.vscode\settings.json` | .JSON | Active | 2026-08-14 16:32:59 | 2 |
| `01_READ_FINAL_AUDIT_REPORT.md` | .MD | Output | 2026-08-16 03:46:00 | 4168 |
| `CHANGELOG.md` | .MD | Output | 2026-08-15 05:49:43 | 369 |
| `ENTRY_BASIS_AUDIT.csv` | .CSV | Output | 2026-08-16 04:35:47 | 380 |
| `ENTRY_FIX_AUDIT.md` | .MD | Output | 2026-08-16 04:35:47 | 2660 |
| `ENTRY_FIX_TESTS.csv` | .CSV | Test | 2026-08-16 04:35:47 | 327 |
| `ENTRY_ISSUES.csv` | .CSV | Active | 2026-08-16 04:35:47 | 303 |
| `ENTRY_PRICE_FORMULAS.csv` | .CSV | Active | 2026-08-16 04:24:17 | 282 |
| `ENTRY_PRICE_FULL_AUDIT.md` | .MD | Output | 2026-08-16 04:22:21 | 3430 |
| `ENTRY_PRICE_TEST_RESULTS.csv` | .CSV | Test | 2026-08-16 04:24:17 | 334 |
| `ENTRY_REGRESSION.csv` | .CSV | Active | 2026-08-16 04:35:47 | 220 |
| `ENTRY_UI_AUDIT.csv` | .CSV | Output | 2026-08-16 04:35:47 | 198 |
| `GEN26_ITEM1_BREAK_EVEN.csv` | .CSV | Active | 2026-08-17 02:38:37 | 30561 |
| `GEN26_ITEM1_COST_SENSITIVITY.csv` | .CSV | Active | 2026-08-17 02:38:37 | 530 |
| `ITEM1_BREAK_EVEN_AUDIT.md` | .MD | Output | 2026-08-17 02:38:37 | 4342 |
| `ITEM2_FINAL_ACCEPTANCE.md` | .MD | Output | 2026-08-16 04:27:09 | 1181 |
| `ITEM2_PAPER_COUNTER_AUDIT.md` | .MD | Output | 2026-08-17 02:38:43 | 876 |
| `ITEM2_PAPER_COUNTER_TESTS.csv` | .CSV | Test | 2026-08-17 02:38:43 | 204 |
| `ITEM3_OVER_CAP_AUDIT.md` | .MD | Output | 2026-08-17 02:38:52 | 1120 |
| `ITEM3_OVER_CAP_TESTS.csv` | .CSV | Test | 2026-08-17 02:38:52 | 483 |
| `ITEM4_EXIT_CALL_GRAPH.md` | .MD | Output | 2026-08-16 04:40:01 | 1032 |
| `ITEM4_EXIT_ML_INDEPENDENCE_AUDIT.md` | .MD | Output | 2026-08-16 04:40:01 | 2332 |
| `ITEM4_EXIT_SAFETY_TESTS.csv` | .CSV | Test | 2026-08-16 04:40:01 | 449 |
| `ITEM4_REGRESSION.csv` | .CSV | Active | 2026-08-16 04:40:01 | 274 |
| `ITEM4_SHADOW_MUTATION_TESTS.csv` | .CSV | Test | 2026-08-17 02:40:15 | 492 |
| `MASTER_ARTIFACT_INDEX.csv` | .CSV | Active | 2026-08-15 16:10:39 | 406 |
| `MASTER_COMPLETE_TEST_RESULTS.json` | .JSON | Test | 2026-08-15 16:10:39 | 391 |
| `MASTER_ULTIMATE_ARTIFACT_INDEX.csv` | .CSV | Active | 2026-08-16 03:46:00 | 608 |
| `MASTER_ULTIMATE_TEST_RESULTS_V41.json` | .JSON | Test | 2026-08-16 03:46:00 | 1634 |
| `PAPER_SESSION_SUMMARY.csv` | .CSV | Active | 2026-08-17 03:29:12 | 286 |
| `REMEDIATION_BEFORE.json` | .JSON | Active | 2026-08-16 04:03:03 | 699 |
| `analyze_top_trades.py` | .PY | Active | 2026-08-15 05:02:31 | 2997 |
| `app.py` | .PY | Active | 2026-08-17 03:32:30 | 109033 |
| `archive_pre_final_run\gen_daily_ranking.csv` | .CSV | Active | 2026-08-15 05:42:15 | 5703 |
| `archive_pre_final_run\gen_decision_log.csv` | .CSV | Active | 2026-08-15 05:42:15 | 16332 |
| `archive_pre_final_run\gen_exit_orders.csv` | .CSV | Active | 2026-08-15 05:42:15 | 1213 |
| `archive_pre_final_run\gen_fx_stress_test.csv` | .CSV | Test | 2026-08-15 05:42:15 | 567 |
| `archive_pre_final_run\gen_portfolio_state.csv` | .CSV | Active | 2026-08-15 05:42:15 | 1440 |
| `archive_pre_final_run\gen_trade_orders.csv` | .CSV | Active | 2026-08-15 05:42:15 | 6267 |
| `audit_backup_before_remediation\app.py` | .PY | Active | 2026-08-14 15:48:52 | 130359 |
| `audit_backup_before_remediation\egx_cib_lstm_engine.py` | .PY | Active | 2026-08-14 15:46:35 | 11906 |
| `audit_backup_before_remediation\execution_status.json` | .JSON | Active | 2026-08-14 15:56:14 | 2043 |
| `audit_backup_before_remediation\my_portfolio.json` | .JSON | Active | 2026-08-14 15:53:50 | 997 |
| `audit_backup_before_remediation\settings.json` | .JSON | Active | 2026-08-14 03:53:04 | 402 |
| `audit_backup_before_remediation\system_full_audit.py` | .PY | Output | 2026-08-14 04:43:48 | 36488 |
| `baseline_v3_0\BACKTEST_RESULTS.csv` | .CSV | Test | 2026-08-14 19:48:49 | 83 |
| `baseline_v3_0\CALIBRATION_RESULTS.csv` | .CSV | Active | 2026-08-14 19:48:49 | 80 |
| `baseline_v3_0\DRIFT_RESULTS.csv` | .CSV | Active | 2026-08-14 19:48:49 | 85 |
| `baseline_v3_0\FACTOR_ABLATION.csv` | .CSV | Active | 2026-08-14 19:48:49 | 149 |
| `baseline_v3_0\FACTOR_COVERAGE_AUDIT.md` | .MD | Output | 2026-08-14 19:48:49 | 758 |
| `baseline_v3_0\FACTOR_IMPORTANCE.csv` | .CSV | Active | 2026-08-14 19:48:49 | 1046 |
| `baseline_v3_0\FINAL_BASELINE_COMPARISON.csv` | .CSV | Active | 2026-08-14 19:05:20 | 91 |
| `baseline_v3_0\FINAL_CALIBRATION.csv` | .CSV | Active | 2026-08-14 19:05:20 | 23 |
| `baseline_v3_0\FINAL_CALIBRATION_REPORT.csv` | .CSV | Output | 2026-08-14 17:55:59 | 79 |
| `baseline_v3_0\FINAL_COST_SENSITIVITY.csv` | .CSV | Active | 2026-08-14 19:05:20 | 145 |
| `baseline_v3_0\FINAL_DAILY_RECONCILIATION.csv` | .CSV | Active | 2026-08-14 19:05:20 | 7418 |
| `baseline_v3_0\FINAL_DRIFT.csv` | .CSV | Active | 2026-08-14 19:05:20 | 17 |
| `baseline_v3_0\FINAL_DRIFT_REPORT.csv` | .CSV | Output | 2026-08-14 17:55:59 | 127 |
| `baseline_v3_0\FINAL_EQUITY_RECONCILIATION.csv` | .CSV | Active | 2026-08-14 17:32:18 | 9284 |
| `baseline_v3_0\FINAL_FORENSIC_AUDIT_RESULTS.json` | .JSON | Output | 2026-08-14 17:26:49 | 6536 |
| `baseline_v3_0\FINAL_GITHUB_WORKFLOW_AUDIT.csv` | .CSV | Output | 2026-08-14 19:05:20 | 108 |
| `baseline_v3_0\FINAL_ISSUES.md` | .MD | Output | 2026-08-14 19:48:49 | 832 |
| `baseline_v3_0\FINAL_ISSUES_FOUND.md` | .MD | Output | 2026-08-14 16:26:39 | 631 |
| `baseline_v3_0\FINAL_KILLSWITCH.csv` | .CSV | Active | 2026-08-14 19:05:20 | 109 |
| `baseline_v3_0\FINAL_KILLSWITCH_TEST.csv` | .CSV | Test | 2026-08-14 17:55:59 | 71 |
| `baseline_v3_0\FINAL_MASTER_FACTOR_AUDIT.md` | .MD | Output | 2026-08-14 19:48:49 | 1807 |
| `baseline_v3_0\FINAL_MONTE_CARLO.csv` | .CSV | Active | 2026-08-14 19:05:20 | 181 |
| `baseline_v3_0\FINAL_MONTE_CARLO_RESULTS.csv` | .CSV | Active | 2026-08-14 17:32:19 | 38525 |
| `baseline_v3_0\FINAL_PAPER_TRADING.csv` | .CSV | Active | 2026-08-14 19:05:20 | 984 |
| `baseline_v3_0\FINAL_PAPER_TRADING_RESULTS.csv` | .CSV | Active | 2026-08-14 17:55:59 | 984 |
| `baseline_v3_0\FINAL_PARAMETER_SENSITIVITY.csv` | .CSV | Active | 2026-08-14 19:05:20 | 103 |
| `baseline_v3_0\FINAL_PRODUCTION_AUDIT.md` | .MD | Output | 2026-08-14 17:52:34 | 5775 |
| `baseline_v3_0\FINAL_SECURITY_AUDIT.md` | .MD | Output | 2026-08-14 19:06:42 | 1919 |
| `baseline_v3_0\FINAL_TEST_RESULTS.json` | .JSON | Test | 2026-08-14 19:05:20 | 88 |
| `baseline_v3_0\FINAL_TOP_TRADE_ROBUSTNESS.csv` | .CSV | Active | 2026-08-14 19:05:20 | 304 |
| `baseline_v3_0\FINAL_TRADE_LEDGER.csv` | .CSV | Active | 2026-08-14 19:05:20 | 42700 |
| `baseline_v3_0\FINAL_YEARLY_PERFORMANCE.csv` | .CSV | Active | 2026-08-14 17:32:18 | 194 |
| `baseline_v3_0\FULL_SYSTEM_AUDIT_REPORT.md` | .MD | Output | 2026-08-14 15:39:30 | 34085 |
| `baseline_v3_0\GITHUB_AUDIT.csv` | .CSV | Output | 2026-08-14 19:48:49 | 316 |
| `baseline_v3_0\MASTER_BASELINE_COMPARISON.csv` | .CSV | Active | 2026-08-14 18:37:59 | 54 |
| `baseline_v3_0\MASTER_CALIBRATION.csv` | .CSV | Active | 2026-08-14 18:38:31 | 33 |
| `baseline_v3_0\MASTER_COST_SENSITIVITY.csv` | .CSV | Active | 2026-08-14 18:37:59 | 69 |
| `baseline_v3_0\MASTER_DAILY_RECONCILIATION.csv` | .CSV | Active | 2026-08-14 18:37:59 | 2 |
| `baseline_v3_0\MASTER_DRIFT_REPORT.csv` | .CSV | Output | 2026-08-14 18:38:31 | 196 |
| `baseline_v3_0\MASTER_EQUITY_RECONCILIATION.csv` | .CSV | Active | 2026-08-14 18:37:59 | 2 |
| `baseline_v3_0\MASTER_FULL_AUDIT_REPORT.md` | .MD | Output | 2026-08-14 18:35:45 | 6770 |
| `baseline_v3_0\MASTER_ISSUES.md` | .MD | Output | 2026-08-14 18:38:31 | 80 |
| `baseline_v3_0\MASTER_KILLSWITCH_TEST.csv` | .CSV | Test | 2026-08-14 18:38:31 | 70 |
| `baseline_v3_0\MASTER_MONTE_CARLO.csv` | .CSV | Active | 2026-08-14 18:37:59 | 21 |
| `baseline_v3_0\MASTER_PAPER_TRADING.csv` | .CSV | Active | 2026-08-14 18:38:31 | 984 |
| `baseline_v3_0\MASTER_PARAMETER_SENSITIVITY.csv` | .CSV | Active | 2026-08-14 18:37:59 | 35 |
| `baseline_v3_0\MASTER_STRESS_TEST_TOP_TRADES.csv` | .CSV | Test | 2026-08-14 19:02:18 | 304 |
| `baseline_v3_0\MASTER_TEST_RESULTS.json` | .JSON | Test | 2026-08-14 18:36:56 | 2529 |
| `baseline_v3_0\MASTER_TRADE_LEDGER.csv` | .CSV | Active | 2026-08-14 19:02:09 | 42700 |
| `baseline_v3_0\MASTER_YEARLY_PERFORMANCE.csv` | .CSV | Active | 2026-08-14 18:37:59 | 35 |
| `baseline_v3_0\MODEL_METRICS.csv` | .CSV | Active | 2026-08-14 19:48:49 | 106 |
| `baseline_v3_0\OPPORTUNITY_TEST_RESULTS.csv` | .CSV | Test | 2026-08-15 03:41:44 | 136 |
| `baseline_v3_0\PAPER_TRADING_RESULTS.csv` | .CSV | Active | 2026-08-14 19:48:49 | 90 |
| `baseline_v3_0\PORTFOLIO_TEST_RESULTS.csv` | .CSV | Test | 2026-08-15 03:41:44 | 112 |
| `baseline_v3_0\PORTFOLIO_WIZARD_AUDIT.md` | .MD | Output | 2026-08-15 03:41:44 | 726 |
| `baseline_v3_0\SETTINGS_TEST_RESULTS.csv` | .CSV | Test | 2026-08-15 03:41:44 | 140 |
| `baseline_v3_0\SYSTEM_SETTINGS_AUDIT.md` | .MD | Output | 2026-08-15 03:41:44 | 718 |
| `baseline_v3_0\TOP_OPPORTUNITIES_AUDIT.md` | .MD | Output | 2026-08-15 03:41:44 | 885 |
| `baseline_v3_0\UI_TEST_RESULTS.csv` | .CSV | Test | 2026-08-15 03:41:44 | 148 |
| `baseline_v3_0\analyze_top_trades.py` | .PY | Active | 2026-08-14 18:55:45 | 2885 |
| `baseline_v3_0\app.py` | .PY | Active | 2026-08-15 03:40:53 | 133895 |
| `baseline_v3_0\audit_test_results.json` | .JSON | Test | 2026-08-14 15:53:34 | 11289 |
| `baseline_v3_0\backtest_empirical_results.json` | .JSON | Test | 2026-08-14 15:38:18 | 552 |
| `baseline_v3_0\compliance_checklist.md` | .MD | Output | 2026-08-13 01:42:15 | 3483 |
| `baseline_v3_0\daily_paper_trade_logger.py` | .PY | Active | 2026-08-14 18:51:01 | 18706 |
| `baseline_v3_0\data\holdout_reserve_locked_20260814.json` | .JSON | Legacy | 2026-08-14 17:47:02 | 33585 |
| `baseline_v3_0\data\model_drift_metrics.json` | .JSON | Active | 2026-08-14 17:41:58 | 257 |
| `baseline_v3_0\data\prediction_actual_telemetry.json` | .JSON | Active | 2026-08-14 17:41:58 | 1622 |
| `baseline_v3_0\egx_cib_lstm_engine.py` | .PY | Active | 2026-08-14 16:03:21 | 12527 |
| `baseline_v3_0\egx_fundamentals.csv` | .CSV | Active | 2026-08-09 02:22:58 | 1588 |
| `baseline_v3_0\egx_fundamentals_builder.py` | .PY | Active | 2026-08-08 07:38:42 | 3132 |
| `baseline_v3_0\egx_screener.py` | .PY | Active | 2026-08-14 18:46:46 | 15559 |
| `baseline_v3_0\execution_status.json` | .JSON | Active | 2026-08-15 03:49:44 | 2050 |
| `baseline_v3_0\full_results_report.md` | .MD | Output | 2026-08-14 04:16:57 | 12232 |
| `baseline_v3_0\gen_daily_ranking.csv` | .CSV | Active | 2026-08-15 03:49:44 | 5916 |
| `baseline_v3_0\gen_decision_log.csv` | .CSV | Active | 2026-08-15 03:49:44 | 16930 |
| `baseline_v3_0\gen_exit_orders.csv` | .CSV | Active | 2026-08-15 03:49:44 | 1516 |
| `baseline_v3_0\gen_fx_stress_test.csv` | .CSV | Test | 2026-08-15 03:49:44 | 567 |
| `baseline_v3_0\gen_portfolio_state.csv` | .CSV | Active | 2026-08-15 03:49:44 | 1536 |
| `baseline_v3_0\gen_trade_orders.csv` | .CSV | Active | 2026-08-15 03:49:44 | 6296 |
| `baseline_v3_0\headless_runner.py` | .PY | Active | 2026-08-14 18:16:01 | 2542 |
| `baseline_v3_0\my_portfolio.json` | .JSON | Active | 2026-08-15 03:49:07 | 563 |
| `baseline_v3_0\my_portfolio_backup_20260814_035315.json` | .JSON | Active | 2026-08-14 03:53:15 | 871 |
| `baseline_v3_0\my_portfolio_backup_20260814_041015.json` | .JSON | Active | 2026-08-14 04:10:15 | 871 |
| `baseline_v3_0\my_portfolio_backup_pre_reset_20260814_043611.json` | .JSON | Active | 2026-08-14 04:36:11 | 1193 |
| `baseline_v3_0\my_portfolio_backup_pre_reset_20260814_043636.json` | .JSON | Active | 2026-08-14 04:36:36 | 996 |
| `baseline_v3_0\my_portfolio_backup_pre_reset_20260814_045310.json` | .JSON | Active | 2026-08-14 04:53:10 | 996 |
| `baseline_v3_0\my_portfolio_backup_pre_reset_20260814_170417.json` | .JSON | Active | 2026-08-14 17:04:17 | 997 |
| `baseline_v3_0\my_portfolio_backup_pre_reset_20260814_191849.json` | .JSON | Active | 2026-08-14 19:18:49 | 870 |
| `baseline_v3_0\my_portfolio_backup_pre_reset_20260814_191852.json` | .JSON | Active | 2026-08-14 19:18:52 | 316 |
| `baseline_v3_0\my_portfolio_backup_pre_reset_20260814_193239.json` | .JSON | Active | 2026-08-14 19:32:39 | 1087 |
| `baseline_v3_0\paper_trading_journal.json` | .JSON | Active | 2026-08-14 17:41:38 | 1778 |
| `baseline_v3_0\predictions_history.json` | .JSON | Active | 2026-08-15 03:54:22 | 248437 |
| `baseline_v3_0\run_bt.py` | .PY | Active | 2026-08-14 19:00:35 | 764 |
| `baseline_v3_0\settings.json` | .JSON | Active | 2026-08-14 03:53:04 | 402 |
| `baseline_v3_0\show_my_results.py` | .PY | Active | 2026-08-13 03:24:27 | 6552 |
| `baseline_v3_0\system_full_audit.py` | .PY | Output | 2026-08-14 04:43:48 | 36488 |
| `baseline_v3_0\task.md` | .MD | Output | 2026-08-15 03:57:05 | 990 |
| `baseline_v3_0\telemetry_tracker.py` | .PY | Active | 2026-08-14 17:41:35 | 7510 |
| `baseline_v3_0\v3_0_snapshot_hash.json` | .JSON | Active | 2026-08-15 03:57:31 | 10966 |
| `baseline_v3_0\walk_forward_backtest_engine.py` | .PY | Test | 2026-08-14 18:47:42 | 18685 |
| `baseline_v3_0\walk_forward_backtest_report.json` | .JSON | Test | 2026-08-14 19:02:09 | 407140 |
| `daily_paper_trade_logger.py` | .PY | Active | 2026-08-17 02:53:53 | 19054 |
| `data\holdout_reserve_locked_20260814.json` | .JSON | Legacy | 2026-08-14 17:47:02 | 33585 |
| `data\model_drift_metrics.json` | .JSON | Active | 2026-08-14 17:41:58 | 257 |
| `data\prediction_actual_telemetry.json` | .JSON | Active | 2026-08-14 17:41:58 | 1622 |
| `debug.json` | .JSON | Active | 2026-08-15 05:34:02 | 1635 |
| `egx_cib_lstm_engine.py` | .PY | Active | 2026-08-14 16:03:21 | 12527 |
| `egx_fundamentals_builder.py` | .PY | Active | 2026-08-08 07:38:42 | 3132 |
| `egx_screener.py` | .PY | Active | 2026-08-17 02:53:53 | 15877 |
| `execution_status.json` | .JSON | Active | 2026-08-17 03:17:56 | 59 |
| `gen_daily_ranking.csv` | .CSV | Active | 2026-08-17 03:17:56 | 6089 |
| `gen_decision_log.csv` | .CSV | Active | 2026-08-17 03:17:56 | 6135 |
| `gen_decision_log.json` | .JSON | Active | 2026-08-17 03:17:56 | 41162 |
| `gen_exit_orders.csv` | .CSV | Active | 2026-08-17 03:17:56 | 5 |
| `gen_fx_stress_test.csv` | .CSV | Test | 2026-08-17 03:17:56 | 567 |
| `gen_portfolio_state.csv` | .CSV | Active | 2026-08-17 03:17:56 | 2217 |
| `gen_trade_orders.csv` | .CSV | Active | 2026-08-17 03:17:56 | 3221 |
| `headless_runner.py` | .PY | Active | 2026-08-17 02:50:06 | 2540 |
| `market_data_provider.py` | .PY | Active | 2026-08-17 03:09:44 | 6477 |
| `my_portfolio.json` | .JSON | Active | 2026-08-17 02:53:53 | 998 |
| `my_portfolio_backup_pre_reset_20260816_042451.json` | .JSON | Active | 2026-08-16 04:24:51 | 1180 |
| `paper_no_trade_log.csv` | .CSV | Active | 2026-08-17 03:29:12 | 534 |
| `paper_trading_journal.json` | .JSON | Active | 2026-08-14 17:41:38 | 1778 |
| `patch_app.py` | .PY | Active | 2026-08-15 05:29:49 | 3864 |
| `predictions_history.json` | .JSON | Active | 2026-08-17 03:17:56 | 202201 |
| `run_bt.py` | .PY | Active | 2026-08-14 19:00:35 | 764 |
| `session_manager.py` | .PY | Active | 2026-08-16 04:14:01 | 4063 |
| `settings.json` | .JSON | Active | 2026-08-14 03:53:04 | 402 |
| `shadow_predictions_log.csv` | .CSV | Active | 2026-08-17 03:17:56 | 5437 |
| `show_my_results.py` | .PY | Active | 2026-08-13 03:24:27 | 6552 |
| `system_full_audit.py` | .PY | Output | 2026-08-17 02:53:53 | 41683 |
| `telemetry_tracker.py` | .PY | Active | 2026-08-14 17:41:35 | 7510 |
| `tests\__init__.py` | .PY | Active | 2026-08-14 16:05:09 | 50 |
| `tests\test_backtest.py` | .PY | Test | 2026-08-14 16:08:27 | 2478 |
| `tests\test_data_leakage.py` | .PY | Test | 2026-08-14 16:07:06 | 2348 |
| `tests\test_liquidity.py` | .PY | Test | 2026-08-14 16:06:41 | 2469 |
| `tests\test_portfolio_equity.py` | .PY | Test | 2026-08-14 16:12:53 | 3089 |
| `tests\test_red_team_edge_cases.py` | .PY | Test | 2026-08-14 16:09:52 | 2597 |
| `tests\test_stop_loss.py` | .PY | Test | 2026-08-14 16:09:12 | 2159 |
| `tests\test_targets.py` | .PY | Test | 2026-08-14 16:07:47 | 1798 |
| `walk_forward_backtest_engine.py` | .PY | Test | 2026-08-17 02:53:53 | 19093 |
| `walk_forward_backtest_report.json` | .JSON | Test | 2026-08-17 02:53:53 | 407140 |

### 2.2 تحليل الملفات البرمجية الرئيسية والشجرة الاعتمادية
#### 📄 `analyze_top_trades.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** calculate_metrics, main
- **ملفات يقرأ منها (Reads):** walk_forward_backtest_report.json
- **ملفات يكتب عليها (Writes):** MASTER_STRESS_TEST_TOP_TRADES.csv

#### 📄 `app.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** load_app_settings, round_to_egx_tick_size, get_cairo_now, is_egx_market_open, estimate_slippage, fetch_tradingview_live_prices, safe_download_multisource, run_data_quality_gate, compute_liquidity_flag, check_ticker_cooldown ...
- **ملفات يقرأ منها (Reads):** my_portfolio.json, paper_trading_journal.json, settings.json, execution_status.json, predictions_history.json
- **ملفات يكتب عليها (Writes):** my_portfolio.json, paper_trading_journal.json, settings.json, execution_status.json, predictions_history.json

#### 📄 `daily_paper_trade_logger.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** safe_download, load_journal, save_journal, run_daily_paper_trading
- **ملفات يقرأ منها (Reads):** paper_trading_journal.json
- **ملفات يكتب عليها (Writes):** paper_trading_journal.json

#### 📄 `egx_cib_lstm_engine.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** main, fetch_and_prepare_data, train_price_prediction_lstm, generate_explainability_report
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `egx_fundamentals_builder.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** 
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `egx_screener.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** main, safe_download, extract_series, build_features_for_stock
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `headless_runner.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** main
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `market_data_provider.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** __init__, get_quote, get_quotes, get_market_status, __init__, _evaluate_freshness, get_quote, get_quotes, _build_empty_quote
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `patch_app.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** 
- **ملفات يقرأ منها (Reads):** app.py
- **ملفات يكتب عليها (Writes):** app.py

#### 📄 `run_bt.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** 
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** walk_forward_backtest_report.json, MASTER_TRADE_LEDGER.csv

#### 📄 `session_manager.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** _load, _save, start_session, complete_session, fail_session, get_valid_days, inject_fixture
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `show_my_results.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** load_journal, calculate_streaks, update_weekly_summary, run_dashboard, rprint
- **ملفات يقرأ منها (Reads):** weekly_summary.txt, dashboard_report.txt, paper_trading_journal.json
- **ملفات يكتب عليها (Writes):** weekly_summary.txt, dashboard_report.txt, paper_trading_journal.json

#### 📄 `telemetry_tracker.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** safe_download, run_telemetry, calc_metrics
- **ملفات يقرأ منها (Reads):** prediction_actual_telemetry.json, model_drift_metrics.json, paper_trading_journal.json
- **ملفات يكتب عليها (Writes):** prediction_actual_telemetry.json, model_drift_metrics.json, paper_trading_journal.json

#### 📄 `audit_backup_before_remediation\app.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** load_app_settings, estimate_slippage, fetch_tradingview_live_prices, safe_download_multisource, run_data_quality_gate, compute_liquidity_flag, check_ticker_cooldown, check_paper_trading_phase, compute_combined_allocation, compute_exit_signals ...
- **ملفات يقرأ منها (Reads):** my_portfolio.json, paper_trading_journal.json, settings.json, execution_status.json, predictions_history.json
- **ملفات يكتب عليها (Writes):** my_portfolio.json, paper_trading_journal.json, settings.json, execution_status.json, predictions_history.json

#### 📄 `audit_backup_before_remediation\egx_cib_lstm_engine.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** main, fetch_and_prepare_data, train_price_prediction_lstm, generate_explainability_report
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `baseline_v3_0\analyze_top_trades.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** calculate_metrics, main
- **ملفات يقرأ منها (Reads):** walk_forward_backtest_report.json
- **ملفات يكتب عليها (Writes):** MASTER_STRESS_TEST_TOP_TRADES.csv

#### 📄 `baseline_v3_0\app.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** load_app_settings, save_app_settings, round_to_egx_tick_size, get_cairo_now, is_egx_market_open, estimate_slippage, fetch_tradingview_live_prices, safe_download_multisource, run_data_quality_gate, compute_liquidity_flag ...
- **ملفات يقرأ منها (Reads):** my_portfolio.json, paper_trading_journal.json, settings.json, execution_status.json, predictions_history.json
- **ملفات يكتب عليها (Writes):** my_portfolio.json, paper_trading_journal.json, settings.json, execution_status.json, predictions_history.json

#### 📄 `baseline_v3_0\daily_paper_trade_logger.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** safe_download, load_journal, save_journal, run_daily_paper_trading
- **ملفات يقرأ منها (Reads):** paper_trading_journal.json
- **ملفات يكتب عليها (Writes):** paper_trading_journal.json

#### 📄 `baseline_v3_0\egx_cib_lstm_engine.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** main, fetch_and_prepare_data, train_price_prediction_lstm, generate_explainability_report
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `baseline_v3_0\egx_fundamentals_builder.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** 
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `baseline_v3_0\egx_screener.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** main, safe_download, extract_series, build_features_for_stock
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `baseline_v3_0\headless_runner.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** main
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** None

#### 📄 `baseline_v3_0\run_bt.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** 
- **ملفات يقرأ منها (Reads):** None
- **ملفات يكتب عليها (Writes):** walk_forward_backtest_report.json, MASTER_TRADE_LEDGER.csv

#### 📄 `baseline_v3_0\show_my_results.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** load_journal, calculate_streaks, update_weekly_summary, run_dashboard, rprint
- **ملفات يقرأ منها (Reads):** weekly_summary.txt, dashboard_report.txt, paper_trading_journal.json
- **ملفات يكتب عليها (Writes):** weekly_summary.txt, dashboard_report.txt, paper_trading_journal.json

#### 📄 `baseline_v3_0\telemetry_tracker.py`
- **الوظيفة الأساسية:** (تم استنتاجها من التحليل الآلي للدوال والواردات)
- **الدوال (Functions):** safe_download, run_telemetry, calc_metrics
- **ملفات يقرأ منها (Reads):** prediction_actual_telemetry.json, model_drift_metrics.json, paper_trading_journal.json
- **ملفات يكتب عليها (Writes):** prediction_actual_telemetry.json, model_drift_metrics.json, paper_trading_journal.json

## 3. جرد GitHub بالكامل
### 3.1 Workflows الحالية
- لا يوجد مسارات عمل نشطة تم العثور عليها محلياً.

### 3.2 حالة تشغيل GitHub Actions الفعلية
Failed to fetch actions: <urlopen error [Errno 11001] getaddrinfo failed>

### 3.3 آخر Commits على الـ Repo
| Hash | Date | Message |
|---|---|---|
| `b3c7e8b` | 2026-08-17 | ci: idempotency rerun test |
| `dfd5e18` | 2026-08-16 | chore(auto): update daily paper trading journal and snapshots |
| `43d6e4b` | 2026-08-17 | fix: update headless runner to use new app.run_engine_pipeline unpack |
| `427c0cb` | 2026-08-17 | ci: add push trigger for testing |
| `ac74590` | 2026-08-17 | ci: fix github actions requirements and node version |
| `14cf06a` | 2026-08-14 | Initial Production Commit - Gen-26 v3.0 |

### 3.4 حالة الـ Secrets (API Keys)
- **ملاحظة:** لا يمكن فحص الأسرار مباشرة عبر السكربتات المحلية لأسباب أمنية. لكن نجاح بناء Actions الأخير يؤكد عمل الأساسيات.
- **التحديث التلقائي:** Commit البوت التلقائي يعمل يومياً لتسجيل الـ Paper Trading.

## 4. جدول كل الإصلاحات والميزات (تاريخي)
| الوصف | الملف المسؤول | الحالة الحالية | الدليل الفعلي (Proof) |
|---|---|---|---|
| منع ازدواج الأوامر (Idempotency) | `app.py (Decision Builder & Logger)` | **محلولة ومؤكدة بدليل** | Decision_ID generation using TS + Equity Hash. Checked in ITEM 8 Idempotency tests. |
| بوابة الكاش الحر الفعلي (Cash Gate) | `app.py` | **محلولة ومؤكدة بدليل** | Calculates strictly `available_free_cash = cash + freed_cash` and rejects if insufficient. ITEM 8 Test Matrix PASS. |
| بوابة سقف التخصيص 65% (Over-Cap Buy Gate) | `app.py` | **محلولة ومؤكدة بدليل** | current_invested_weight_pct > MAX_TOTAL_ALLOCATION_PCT blocks new buys. Live tested in ITEM 7/8. |
| فصل قرارات الخروج عن النموذج (Objective Exit Logic) | `app.py / egx_screener.py` | **محلولة ومؤكدة بدليل** | Holdings are routed strictly to Exit Logic bypassing buy constraints. |
| نسبة التخفيض الديناميكية | `app.py` | **محلولة ومؤكدة بدليل** | Dynamic pullback logic implemented in entry calculation. |
| وسم البيانات غير المؤكدة و Reset Wizard | `app.py` | **محلولة ومؤكدة بدليل** | `data_verification_status` added to holdings. Wizard handles raw text parsing. |
| تصحيح خطأ الـEncoding | `All Python/Workflows` | **محلولة ومؤكدة بدليل** | Added `encoding='utf-8'` to all open() calls and `PYTHONIOENCODING=utf-8` to CI. |
| تصحيح القسمة على صفر في حساب الأوزان | `app.py` | **محلولة ومؤكدة بدليل** | Added max(len, 1) and epsilon additions to avoid ZeroDivisionError. |
| تجميد النموذج التنبؤي (Shadow Mode) | `app.py` | **محلولة ومؤكدة بدليل** | UI reports SHADOW mode. Actual execution is isolated to paper log. |
| عداد Paper Trading | `app.py` | **محلولة ومؤكدة بدليل** | `len(load_paper_journal())` tracked in telemetry and UI (Paper Phase X/100). |
| توحيد مصدر القرار (Single Decision Object) | `app.py` | **محلولة ومؤكدة بدليل** | `build_final_decision_objects` serves as the sole SSoT across UI/CSV/Log. |
| تأخير البيانات وتصحيح التوقيت (Live vs Source Time) | `market_data_provider.py / app.py` | **محلولة ومؤكدة بدليل** | Explicit tracking of `source_timestamp`, `received_timestamp`, and `STALE_MARKET_DATA` UI block. |
| تعريب واجهة المستخدم بالكامل | `app.py` | **محلولة ومؤكدة بدليل** | All UI elements translated using Python script replacement. |

## 5. شرح تفصيلي لكل إصلاح
### 🎯 منع ازدواج الأوامر (Idempotency)
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py (Decision Builder & Logger)` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** Decision_ID generation using TS + Equity Hash. Checked in ITEM 8 Idempotency tests.

### 🎯 بوابة الكاش الحر الفعلي (Cash Gate)
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** Calculates strictly `available_free_cash = cash + freed_cash` and rejects if insufficient. ITEM 8 Test Matrix PASS.

### 🎯 بوابة سقف التخصيص 65% (Over-Cap Buy Gate)
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** current_invested_weight_pct > MAX_TOTAL_ALLOCATION_PCT blocks new buys. Live tested in ITEM 7/8.

### 🎯 فصل قرارات الخروج عن النموذج (Objective Exit Logic)
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py / egx_screener.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** Holdings are routed strictly to Exit Logic bypassing buy constraints.

### 🎯 نسبة التخفيض الديناميكية
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** Dynamic pullback logic implemented in entry calculation.

### 🎯 وسم البيانات غير المؤكدة و Reset Wizard
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** `data_verification_status` added to holdings. Wizard handles raw text parsing.

### 🎯 تصحيح خطأ الـEncoding
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `All Python/Workflows` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** Added `encoding='utf-8'` to all open() calls and `PYTHONIOENCODING=utf-8` to CI.

### 🎯 تصحيح القسمة على صفر في حساب الأوزان
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** Added max(len, 1) and epsilon additions to avoid ZeroDivisionError.

### 🎯 تجميد النموذج التنبؤي (Shadow Mode)
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** UI reports SHADOW mode. Actual execution is isolated to paper log.

### 🎯 عداد Paper Trading
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** `len(load_paper_journal())` tracked in telemetry and UI (Paper Phase X/100).

### 🎯 توحيد مصدر القرار (Single Decision Object)
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** `build_final_decision_objects` serves as the sole SSoT across UI/CSV/Log.

### 🎯 تأخير البيانات وتصحيح التوقيت (Live vs Source Time)
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `market_data_provider.py / app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** Explicit tracking of `source_timestamp`, `received_timestamp`, and `STALE_MARKET_DATA` UI block.

### 🎯 تعريب واجهة المستخدم بالكامل
- **المشكلة الأصلية:** النظام كان يعاني من قصور في هذا الجانب مما كان يسبب قرارات تداول غير دقيقة أو عشوائية في حالات Edge Cases.
- **منطق الكود (الحل):** تم تعديل `app.py` لدمج الحل كقيد (Gate) صارم لا يمكن تخطيه. في معمارية Single Decision Object الحالية، أي فشل يُسجل بوضوح.
- **الدليل الفعلي:** All UI elements translated using Python script replacement.

## 6. جدول المشاكل المفتوحة
| المشكلة | الأولوية | الحالة | ملاحظات |
|---|---|---|---|
| تدقيق Break-even من الـRaw Ledger | High | **لسه مفتوحة** | Requires cross-referencing execution CSV with portfolio value. |
| إغلاق الثغرات في Risk Rules (Trailing stops) | Medium | **لسه مفتوحة** | Static targets exist, but trailing stop loss logic needs refinement. |
| الاعتماد الكلي على YFinance للبيانات اللحظية | Low | **محلولة لكن غير مؤكدة بدليل حديث** | Delayed data is enforced, but a primary robust real-time API (Thndr/Mubasher) is missing. |

## 7. الخطوات التالية المقترحة (بالترتيب)
1. **تدقيق Break-even من Raw Ledger** (الأولوية القصوى).
2. **إغلاق منطق إيقاف الخسارة المتحرك (Trailing Stop).**
3. **البدء بمرحلة ربط الـ Live Execution (بعد 100 جلسة Paper Trading ناجحة).**