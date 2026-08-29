# 20. Master Index, System Glossary & Executive Sign-Off

## 1. Master Index of Authoritative Reports

| # | Document Filename | Domain Focus | Key Architectural Artifact |
| :--- | :--- | :--- | :--- |
| **01** | `01_SYSTEM_ARCHITECTURE_OVERVIEW.md` | System Stack | 5-Layer Stack Architecture & Data Flow |
| **02** | `02_EGX_244_UNIVERSE_CATALOG.md` | Universe | 244-Stock EGX Catalog & Liquidity Gate |
| **03** | `03_MACRO_REGIME_AND_CBE_CORRIDOR.md` | Macroeconomics | CBE 19.0% Rate, Inflation, Hurdle Rate |
| **04** | `04_DATABASE_SCHEMA_AND_PERSISTENCE.md` | Database | SQLite WAL Schema & Persistence Engine |
| **05** | `05_SEVEN_AGENT_QUANT_COUNCIL.md` | Multi-Agent AI | 7-Agent Council Consensus & Veto Rules |
| **06** | `06_AUTONOMOUS_RESEARCH_LAB.md` | Auto-Research | Continuous Hypothesis & Learning Loop |
| **07** | `07_PURGED_WALK_FORWARD_PROMOTION_GATE.md`| Validation | Purged Cross-Validation & DSR Promotion |
| **08** | `08_EPISODIC_FAILURE_MEMORY.md` | Risk Memory | Failure Quarantine & Lessons Learned |
| **09** | `09_PIOTROSKI_F_SCORE_ANALYSIS.md` | Fundamental | 9-Point Accounting Quality Framework |
| **10** | `10_PETER_LYNCH_VALUATION_METRICS.md` | Valuation | PEG Ratios, Net Cash & 6 Stock Types |
| **11** | `11_NISON_CANDLESTICKS_AND_MURPHY_TECH.md`| Technical | Japanese Candles, ADX & Fibonacci Levels |
| **12** | `12_MARK_DOUGLAS_PSYCHOLOGY_GUARD.md` | Psychology/Risk | 24h Lockout, $R:R \ge 1:2.5$, Trailing Stops |
| **13** | `13_LONDON_GDR_ARBITRAGE_REPORT.md` | Dual Listings | London GDR Parity & Implied USD/EGP |
| **14** | `14_STATISTICAL_PAIRS_ARBITRAGE.md` | Stat-Arb | Cointegration, Z-Score & Half-Life Mean Rev|
| **15** | `15_DEEP_QUANT_48_FEATURE_TENSOR.md` | Feature Eng | 48-Dimensional Normalized Quant Tensor |
| **16** | `16_TWO_STAGE_META_LABELING_AI.md` | Machine Learning| López de Prado Two-Stage Meta-Labeling |
| **17** | `17_EGX_TRADING_RULES_AND_CGT_TAX.md` | Compliance | Circuit Breakers ($\pm 10\%/\pm 20\%$) & 10% CGT |
| **18** | `18_BLACK_SWAN_STRESS_TESTING.md` | Stress Testing | Tail-Risk Scenarios, VaR, CVaR Defense |
| **19** | `19_DEVOPS_CI_CD_AND_TEST_BATTERY.md` | STLC / DevOps | 17 Test Suites, 456 Tests (100% Pass) |
| **20** | `20_MASTER_INDEX_AND_SYSTEM_GLOSSARY.md`| Governance | Index, Bilingual Glossary, Sign-Off |

---

## 2. Bilingual Quantitative Finance Glossary

| English Term | Arabic Equivalent | Technical Definition |
| :--- | :--- | :--- |
| **Alpha ($\alpha$)** | العائد الإضافي المستقل عن السوق | Active return on an investment above the market benchmark (EGX30). |
| **Beta ($\beta$)** | معامل حساسية السهم للسوق | Measure of the volatility of a security in comparison to the market. |
| **Piotroski F-Score** | مقياس بيوتروسكي لجودة القوائم المالية | 9-point score measuring profitability, leverage, and operating efficiency. |
| **Two-Stage Meta-Labeling** | التصنيف الفوقي ثنائي المراحل | ML framework predicting trade success probability and bet sizing. |
| **Deflated Sharpe Ratio (DSR)** | نسبة شارب المنقحة ضد فرط التخصيص | Sharpe ratio adjusted for selection bias and number of trials. |
| **Purged Cross-Validation** | التحقق المتقاطع المنقى من التسريب الزمني | Cross-validation removing overlapping labels to prevent data leakage. |
| **London GDR Parity** | التكافؤ السعري لشهادات الإيداع بلندن | The theoretical local stock price implied by London dual-listed GDRs. |
| **Circuit Breakers** | قواطع الدائرة وحدود الإيقاف السعري | Regulatory trading halts at $\pm 10\%$ and $\pm 20\%$ price movements. |
| **Capital Gains Tax (CGT)** | ضريبة الأرباح الرأسمالية | $10.0\%$ statutory tax deducted from net realized equity gains. |
| **Drawdown** | أقصى تراجع للمحفظة من القمة | Peak-to-trough decline during a specific record period. |

---

## 3. Executive Architecture Sign-Off

- **Platform Version**: `GEN-26 Institutional Quant Terminal v3.0.0`
- **Universe Coverage**: $244$ Egyptian Equities (Mapped to Thndr & Official ISINs)
- **Quality Assurance**: $456 / 456$ Automated STLC Unit & Integration Tests Passed ($100\%$)
- **Status**: **PRODUCTION CERTIFIED & INSTITUTIONALLY COMPLIANT** (معتمد للإنتاج المؤسسي).
