# FINAL ISSUES FOUND — Gen-26 v3.0 Clean-Room Re-Audit

Total Issues: 5

| # | Section | Test | Severity | Detail |
|---|---|---|---|---|
| 1 | S2_HardcodeGrep | Hardcoded accuracy 63.1 | HIGH | L1534: ho = run_portfolio_equity_holdout_test(full_df, FC) if not full_df.empty else 63.1 |
| 2 | S2_HardcodeGrep | Mock 1.25 Sharpe (could be false positive) | HIGH | L84: font-size: 1.25rem; |
| 3 | S8_RiskGates | Cash gate logic | HIGH |  |
| 4 | S11_CSV | gen_portfolio_state.csv read error | HIGH | slice(None, 120, None) |
| 5 | S11_CSV | gen_daily_ranking.csv missing columns | HIGH | ['الاسم', 'الكود'] |
