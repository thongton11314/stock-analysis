# Market Analysis — System Architecture

## System Overview Diagram

```mermaid
graph TB
    %% ========================================
    %% USER INTERACTION LAYER
    %% ========================================
    User([fa:fa-user User])

    subgraph Triggers["User Triggers"]
        T1["analyze TICKER"]
        T2["short-term signal for TICKER"]
        T3["correction risk for TICKER"]
        T4["simulate events for TICKER"]
        T5["fix the layout"]
        T6["audit report"]
        T7["fetch data for TICKER"]
        T8["analyze TICKER1, TICKER2, TICKER3<br/>(sequential multi-ticker)"]
        T9["validate numbers for TICKER"]
        T10["run tests / verify changes"]
    end

    User --> Triggers

    %% ========================================
    %% AGENT LAYER (two specialized agents)
    %% ========================================
    subgraph Agents["Agent Layer"]
        direction LR
        SA["stock-analyst.agent.md<br/>───────────────────<br/>Orchestrates analysis skills<br/>70+ tools available<br/>Auto-matches skills by description"]
        TE["test-engineer.agent.md<br/>───────────────────<br/>System testing & verification<br/>Runs test suites, diagnoses failures<br/>Manages golden references<br/>Enforces Change Verification Protocol"]
        PM["portfolio-manager.agent.md<br/>───────────────────<br/>Portfolio dashboard builder<br/>Aggregates all analyzed tickers<br/>build_portfolio.py + audit_portfolio.py"]
    end

    Triggers --> Agents

    %% ========================================
    %% SKILL LAYER (13 skills, auto-matched)
    %% ========================================
    subgraph Skills["Skills Layer — Auto-Matched by Description"]
        direction TB

        subgraph DataSkill["Data Collection"]
            DC["data-collection/SKILL.md<br/>──────────────────<br/>MCP API calls<br/>15 subject + peers + macro<br/>Company profile classification<br/>Outputs: Data Bundle"]
        end

        subgraph ComputeSkills["Analyst Compute Engine"]
            direction LR
            ACE["analyst-compute-engine<br/>──────────────────<br/>Unified Python pipeline<br/>analyst_compute_engine.py<br/>Phase 0: pre-flight (135 tests)<br/>validate → compute → validate<br/>Single command, exit codes 0-4<br/>Outputs: Signal JSONs + report"]
        end

        subgraph AnalysisSkills["Standalone Analysis Skills"]
            direction LR
            ST["short-term-analysis<br/>──────────────────<br/>TB/VS/VF gates<br/>Fragility Score 0-5<br/>Outputs: SHORT_TERM_SIGNAL"]
            LT["long-term-prediction<br/>──────────────────<br/>CCRLO scoring 0-21<br/>7 macro-financial features<br/>Outputs: CCRLO_SIGNAL"]
            SIM["simulation<br/>──────────────────<br/>Regime detection<br/>6 events × 3 horizons<br/>4 scenario weights<br/>Outputs: SIMULATION_SIGNAL"]
            TAG["stock-tagging<br/>──────────────────<br/>5-dimension classification<br/>Profile/Sector/Risk/Momentum/Val<br/>Outputs: TAG_SIGNAL"]
        end

        subgraph OutputSkills["Output Skills"]
            direction LR
            RG["report-generation<br/>──────────────────<br/>20-section HTML report<br/>Uses Python-computed signals<br/>Phase 5: post-gen audit (7 layers)<br/>Outputs: HTML file"]
            RF["report-fix<br/>──────────────────<br/>Diagnose & repair<br/>PDF layout, CSS, SVG<br/>Outputs: Fixed HTML"]
            RA["report-audit<br/>──────────────────<br/>7-layer QA check<br/>Standalone deep audit<br/>Outputs: Audit report"]
        end

        subgraph ValidationSkills["Numerical Validation"]
            NA["numerical-audit<br/>──────────────────<br/>3-stage accuracy pipeline<br/>A=data B=signals C=report<br/>validate_numbers.py<br/>Outputs: Numerical audit JSON"]
        end

        subgraph TestSkills["System Testing"]
            SYS["system-test<br/>──────────────────<br/>183 automated tests (6 suites)<br/>Golden reference regression<br/>Docs consistency verification<br/>Live AV pipeline test<br/>Change verification protocol"]
        end
    end

    SA --> DC
    SA --> ACE
    SA --> ST
    SA --> LT
    SA --> SIM
    SA --> RG
    SA --> RF
    SA --> RA
    SA --> NA
    TE --> SYS
    TE --> NA

    %% ========================================
    %% DATA FLOW
    %% ========================================
    subgraph ExternalData["Alpha Vantage MCP Server"]
        AV["TOOL_LIST / TOOL_GET / TOOL_CALL<br/>──────────────────<br/>Stock APIs: GLOBAL_QUOTE, COMPANY_OVERVIEW, etc.<br/>Technical: RSI, MACD, BBANDS, SMA, EMA, ADX, ATR<br/>Macro: CPI, FED_FUNDS, UNEMPLOYMENT, GDP<br/>Sentiment: NEWS_SENTIMENT, INSTITUTIONAL_HOLDINGS"]
    end

    DC -->|"MCP calls"| AV
    AV -->|"Raw data"| DC

    %% ========================================
    %% SIGNAL PIPELINE (data dependencies)
    %% ========================================
    DC -->|"Data Bundle JSON"| ACE
    ACE -->|"Validated Signals"| RG

    DC -->|"Data Bundle"| ST
    DC -->|"Data Bundle"| LT
    DC -->|"Data Bundle"| SIM

    ST -->|"SHORT_TERM_SIGNAL<br/>(fragility feeds SIM)"| SIM
    LT -->|"CCRLO_SIGNAL<br/>(score feeds SIM)"| SIM

    ACE -->|"SHORT_TERM_SIGNAL"| RG
    ACE -->|"CCRLO_SIGNAL"| RG
    ACE -->|"SIMULATION_SIGNAL"| RG

    %% ========================================
    %% LOCAL COMPUTE LAYER
    %% ========================================
    subgraph LocalCompute["Python Scripts (Local Compute)"]
        ENGINE["analyst_compute_engine.py<br/>Unified orchestrator"]
        PY1["compute_short_term.py<br/>TB/VS/VF + Fragility"]
        PY2["compute_ccrlo.py<br/>7 features → Score 0-21"]
        PY3["compute_simulation.py<br/>Regime + Events + Scenarios"]
        VI["validate_inputs.py<br/>Data bundle validation"]
        VO["validate_outputs.py<br/>Signal contract validation"]
        VN["validate_numbers.py<br/>Numerical accuracy audit"]
        PY4["compute_tags.py<br/>5-dimension stock classification"]
        RT["run_tests.py<br/>Unified test runner<br/>183 tests · 6 suites · live AV"]
        BP["build_portfolio.py<br/>Portfolio aggregation + HTML gen"]
        AP["audit_portfolio.py<br/>Portfolio 8-layer audit"]
        PO["portfolio_optimizer.py<br/>Evidence-based construction engine"]
    end

    ACE --> ENGINE
    ENGINE --> VI
    ENGINE --> PY1
    ENGINE --> PY2
    ENGINE --> PY3
    ENGINE --> VO
    NA --> VN
    SYS --> RT
    PM --> BP
    BP --> PO
    BP --> AP

    %% ========================================
    %% REFERENCE LAYER
    %% ========================================
    subgraph References["Reference Documents"]
        direction LR

        subgraph Contracts["Signal Contracts"]
            SC["signal-contracts.md<br/>──────────────────<br/>SHORT_TERM_SIGNAL schema<br/>CCRLO_SIGNAL schema<br/>SIMULATION_SIGNAL schema<br/>Validation rules"]
        end

        subgraph Specs[".instructions/"]
            direction TB
            I1["data-collection.md"]
            I2["report-layout.md"]
            I3["styling.md"]
            I4["analysis-methodology.md"]
            I5["analysis-reference.md"]
            I6["short-term-strategy.md"]
            I7["long-term-strategy.md"]
            I8["simulation-strategy.md"]
        end

        subgraph Templates["Templates & Examples"]
            TP["templates/report-template.html<br/>(CSS source of truth)"]
            EX["examples/HOOD-analysis.html<br/>(Gold standard report)"]
        end
    end

    SC -.->|"defines output schema"| ST
    SC -.->|"defines output schema"| LT
    SC -.->|"defines output schema"| SIM
    SC -.->|"validates signals"| RG

    %% ========================================
    %% OUTPUT LAYER
    %% ========================================
    subgraph Output["Generated Reports"]
        RPT["reports/TICKER-analysis.html<br/>──────────────────<br/>20-section standalone HTML<br/>PDF-exportable (A4 landscape)<br/>All signals integrated"]
    end

    RG -->|"Phase 4: Save"| RPT
    RG -->|"Phase 5: Post-Gen Audit"| RPT
    RF -->|"Fixed report"| RPT
    RA -->|"Audit findings"| RPT

    %% ========================================
    %% STYLING
    %% ========================================
    classDef agent fill:#1b2a4a,stroke:#1b2a4a,color:#fff
    classDef skill fill:#2563eb,stroke:#1e40af,color:#fff
    classDef data fill:#0891b2,stroke:#0e7490,color:#fff
    classDef signal fill:#7c3aed,stroke:#6d28d9,color:#fff
    classDef output fill:#16a34a,stroke:#15803d,color:#fff
    classDef ref fill:#f59e0b,stroke:#d97706,color:#000
    classDef external fill:#dc2626,stroke:#b91c1c,color:#fff
    classDef user fill:#6366f1,stroke:#4f46e5,color:#fff
    classDef compute fill:#059669,stroke:#047857,color:#fff
    classDef validate fill:#d97706,stroke:#b45309,color:#fff

    classDef test fill:#0ea5e9,stroke:#0284c7,color:#fff

    class SA,TE agent
    class DC data
    class ST,LT,SIM signal
    class RG,RF,RA skill
    class RPT output
    class AV external
    class SC,I1,I2,I3,I4,I5,I6,I7,I8,TP,EX ref
    class User user
    class ACE,ENGINE,PY1,PY2,PY3 compute
    class VI,VO,VN,NA validate
    class SYS,RT test
```

## Signal Pipeline (Sequential Dependencies)

```mermaid
flowchart LR
    subgraph Phase1["Phase 1: Data Collection"]
        MCP["Alpha Vantage MCP"] --> DB["Data Bundle<br/>15 subject + peers + macro"]
    end

    subgraph Phase1b["Phase 1b: Numerical Audit Stage A"]
        DB --> VNA["validate_numbers.py --stage A<br/>Price math, financials, freshness"]
        VNA -->|"FAIL (exit 1)"| FIXDATA["Fix data bundle"]
        FIXDATA --> VNA
        VNA -->|"PASS"| ENGINE2["Ready for compute"]
    end

    subgraph Phase2["Phase 2: Analyst Compute Engine"]
        ENGINE2 --> ENGINE["analyst_compute_engine.py<br/>(single command)"]

        subgraph Validate1["Input Validation"]
            ENGINE --> VI["validate_inputs.py"]
            VI -->|"FAIL (exit 1)"| REFETCH["Re-fetch & Retry"]
            REFETCH --> VI
            VI -->|"PASS"| COMPUTE
        end

        subgraph Compute["Signal Computation"]
            COMPUTE["validated bundle"] --> PY_ST["compute_short_term.py"]
            COMPUTE --> PY_LT["compute_ccrlo.py"]
            PY_ST -->|"fragility"| PY_SIM["compute_simulation.py"]
            PY_LT -->|"CCRLO"| PY_SIM
        end

        subgraph Validate2["Output Validation"]
            PY_ST --> VO["validate_outputs.py"]
            PY_LT --> VO
            PY_SIM --> VO
            VO -->|"FAIL (exit 3)"| FIX["Review & Fix"]
            FIX --> VO
            VO -->|"PASS (exit 0)"| SIGNALS["Validated Signal JSONs"]
        end
    end

    subgraph Phase2b["Phase 2b: Numerical Audit Stage B"]
        SIGNALS --> VNB["validate_numbers.py --stage B<br/>Gate math, composite sums, cross-signal"]
        VNB -->|"FAIL (exit 2)"| FIXSIG["Review & fix signals"]
        FIXSIG --> VNB
        VNB -->|"PASS"| SIGREADY["Signals ready for HTML"]
    end

    subgraph Phase3["Phase 3: HTML Generation"]
        SIGREADY --> HTML["20-Section Report"]
    end

    subgraph Phase45["Phase 4-5: Save & Audit"]
        HTML --> SAVE["Save to reports/"]
        SAVE --> VNC["validate_numbers.py --stage C<br/>Report numbers match source"]
        VNC -->|"FAIL (exit 3)"| FIXRPT["Fix report numbers"]
        FIXRPT --> VNC
        VNC -->|"PASS"| AUDIT["Post-Gen Audit<br/>7 critical layers"]
        AUDIT -->|"PASS"| DONE["Ready to Publish"]
        AUDIT -->|"FAIL"| AUTOFIX["Auto-Fix & Re-Audit"]
        AUTOFIX --> AUDIT
    end

    style Phase1 fill:#f0f9ff,stroke:#bae6fd
    style Phase1b fill:#fffbeb,stroke:#fde68a
    style Phase2 fill:#f0fdf4,stroke:#bbf7d0
    style Phase2b fill:#fffbeb,stroke:#fde68a
    style Phase3 fill:#faf5ff,stroke:#e9d5ff
    style Phase45 fill:#fff1f2,stroke:#fecdd3
```

## Signal Cross-Section Mapping

Shows which signal fields appear in which report sections.

```mermaid
graph LR
    subgraph Signals["Signal Contracts"]
        TB["TB/VS/VF + Fragility"]
        CC["CCRLO Score"]
        SIM["Regime + Events"]
    end

    subgraph Sections["Report Sections"]
        S3["Section 3<br/>Executive Summary"]
        S5["Section 5<br/>Price Corridors"]
        S11["Section 11<br/>Technical Indicators"]
        S12["Section 12<br/>Event Risk Viz"]
        S13["Section 13<br/>Risks & Catalysts"]
        S18["Section 18<br/>Macro Scorecard"]
    end

    TB -->|"TB✓/✗ + Fragility badge"| S3
    TB -->|"Prob adjustment if ≥3"| S5
    TB -->|"Status & Score tiles"| S11
    TB -->|"HIGH dims → risks"| S13

    CC -->|"Score + probability"| S3
    CC -->|"Corridor width"| S5
    CC -->|"Composite tile"| S18

    SIM -->|"Regime badge + top event"| S3
    SIM -->|"Tail weight → probs"| S5
    SIM -->|"Regime + Event tiles"| S11
    SIM -->|"Full visualization"| S12
    SIM -->|"Scenario narratives"| S13
    SIM -->|"Event Risk tile"| S18

    style TB fill:#3b82f6,color:#fff
    style CC fill:#8b5cf6,color:#fff
    style SIM fill:#ec4899,color:#fff
    style S3 fill:#f8fafc,stroke:#e2e8f0
    style S5 fill:#f8fafc,stroke:#e2e8f0
    style S11 fill:#f8fafc,stroke:#e2e8f0
    style S12 fill:#f8fafc,stroke:#e2e8f0
    style S13 fill:#f8fafc,stroke:#e2e8f0
    style S18 fill:#f8fafc,stroke:#e2e8f0
```

## Skill Trigger Routing

Shows how user commands map to skills via description-based auto-matching.

```mermaid
flowchart LR
    subgraph UserCommands["User Commands"]
        C1["'analyze AMZN'<br/>'generate report'"]
        C1b["'analyze AMZN, NVDA, MSFT'<br/>'batch analysis'"]
        C2["'fetch data for NVDA'<br/>'collect market data'"]
        C3["'short-term signal for TSLA'<br/>'trend-break analysis'"]
        C4["'correction risk for AAPL'<br/>'CCRLO analysis'"]
        C5["'simulate events for MSFT'<br/>'event risk'"]
        C6["'fix the PDF layout'<br/>'styling bug'"]
        C7["'audit SCHW report'<br/>'validate report'"]
        C8["'compute signals for NVDA'<br/>'validate and compute'"]
        C9["'validate numbers for AMZN'<br/>'numerical audit'"]
        C10["'run tests'<br/>'verify changes'<br/>'did my changes break anything?'"]
        C11["'tag AMZN'<br/>'classify stock'<br/>'stock classification'"]
        C12["'build portfolio'<br/>'portfolio dashboard'"]
        C13["'audit portfolio'<br/>'check portfolio'"]
    end

    subgraph AgentRouting["Agent Routing"]
        AM["Stock Analyst Agent<br/>Description-Based Auto-Match"]
        TM["Test Engineer Agent<br/>Testing & Verification"]
        PM["Portfolio Manager Agent<br/>Dashboard Builder"]
    end

    subgraph MatchedSkills["Matched Skill"]
        S1["report-generation<br/>(sequential per ticker)"]
        S2["data-collection"]
        S3["short-term-analysis"]
        S4["long-term-prediction"]
        S5["simulation"]
        S8["analyst-compute-engine"]
        S6["report-fix"]
        S7["report-audit"]
        S9["numerical-audit"]
        S10["system-test"]
        S11["stock-tagging"]
        S12["portfolio-build"]
        S13["portfolio-audit"]
    end

    C1 --> AM --> S1
    C1b --> AM --> S1
    C2 --> AM --> S2
    C3 --> AM --> S3
    C4 --> AM --> S4
    C5 --> AM --> S5
    C6 --> AM --> S6
    C7 --> AM --> S7
    C8 --> AM --> S8
    C9 --> AM --> S9
    C10 --> TM --> S10
    C11 --> AM --> S11
    C12 --> PM --> S12
    C13 --> PM --> S13

    style AM fill:#1b2a4a,color:#fff
    style TM fill:#0ea5e9,color:#fff
    style PM fill:#7c3aed,color:#fff
    style S1 fill:#16a34a,color:#fff
    style S2 fill:#0891b2,color:#fff
    style S3 fill:#3b82f6,color:#fff
    style S4 fill:#8b5cf6,color:#fff
    style S5 fill:#ec4899,color:#fff
    style S6 fill:#f59e0b,color:#000
    style S7 fill:#ef4444,color:#fff
    style S8 fill:#059669,color:#fff
    style S9 fill:#d97706,color:#fff
    style S10 fill:#0ea5e9,color:#fff
    style S11 fill:#6366f1,color:#fff
    style S12 fill:#7c3aed,color:#fff
    style S13 fill:#a855f7,color:#fff
```

## Full Report Generation Pipeline (End-to-End)

The complete flow for `"analyze TICKER"`:

```mermaid
sequenceDiagram
    actor User
    participant Agent as Stock Analyst Agent
    participant DC as Data Collection Skill
    participant AV as Alpha Vantage MCP
    participant FS as File System
    participant PY as Python Scripts
    participant VN as Numerical Audit
    participant Audit as Post-Gen Audit

    User->>Agent: "analyze AMZN"
    Note over Agent: Auto-matches report-generation skill

    Agent->>DC: Phase 1: Collect Data Bundle
    DC->>AV: TOOL_LIST (core_stock_apis)
    AV-->>DC: Available tools
    DC->>AV: TOOL_CALL × 15 (subject data)
    AV-->>DC: GLOBAL_QUOTE, COMPANY_OVERVIEW, ...
    DC->>AV: TOOL_CALL × 8-10 (peer data)
    AV-->>DC: Peer fundamentals + prices
    DC->>AV: TOOL_CALL × 4 (macro data)
    AV-->>DC: CPI, FED_RATE, UNEMPLOYMENT, GDP
    DC-->>Agent: Data Bundle + Company Profile

    Agent->>FS: Write scripts/data/AMZN_bundle.json

    Note over Agent,VN: Phase 1b: Numerical Audit Stage A (data accuracy)
    Agent->>VN: python validate_numbers.py --ticker AMZN --stage A
    Note over VN: Price math, financial consistency,<br/>data freshness, indicator sanity
    alt Stage A FAIL
        VN-->>Agent: Data issues found
        Agent->>AV: Re-fetch/fix data
        Agent->>VN: Re-run Stage A
    end
    VN-->>Agent: Stage A PASS

    Note over Agent,PY: Phase 2: Analyst Compute Engine (single command)
    Agent->>PY: python scripts/analyst_compute_engine.py --ticker AMZN
    Note over PY: 0. Pre-flight integrity check (135 quick tests)
    Note over PY: 1. validate_inputs.py (data completeness)
    Note over PY: 2. compute_short_term.py → SHORT_TERM
    Note over PY: 3. compute_ccrlo.py → CCRLO
    Note over PY: 4. compute_simulation.py → SIMULATION
    Note over PY: 5. validate_outputs.py (contracts + cross-signal)

    alt Exit code 0 (PASS)
        PY-->>Agent: All signals validated
    else Exit code 4 (Pre-flight FAIL)
        PY-->>Agent: System inconsistency detected
        Note over Agent: Run: python scripts/run_tests.py --suite quick --verbose
        Agent->>PY: Fix inconsistency, re-run engine
    else Exit code 1 (Input FAIL)
        PY-->>Agent: Input validation failed
        Agent->>AV: Re-fetch missing data
        Agent->>FS: Update bundle JSON
        Agent->>PY: Re-run engine
    else Exit code 2-3 (Compute/Output FAIL)
        PY-->>Agent: Check engine_report.json
        Note over Agent: Review blocking_failures
        Agent->>PY: Fix and re-run
    end

    Agent->>FS: Read validated signal JSONs

    Note over Agent,VN: Phase 2b: Numerical Audit Stage B (calculation accuracy)
    Agent->>VN: python validate_numbers.py --ticker AMZN --stage B
    Note over VN: TB/VS/VF gate math, fragility sums,<br/>CCRLO composite, regime/scenario sums,<br/>cross-signal price/date consistency
    alt Stage B FAIL
        VN-->>Agent: Calculation errors found
        Agent->>PY: Fix and re-run engine
        Agent->>VN: Re-run Stage B
    end
    VN-->>Agent: Stage B PASS

    Note over Agent: Phase 3: Generate HTML
    Note over Agent: Copy CSS from report-template.html
    Note over Agent: Build 20 sections in strict order
    Note over Agent: Use Python-computed signals directly
    Note over Agent: SVG corridors, Income Statement Breakdown, monthly forecast,<br/>event risk visualization

    Agent->>FS: Phase 4: Save to reports/AMZN-analysis.html

    Note over Agent,VN: Phase 4b: Numerical Audit Stage C (report numbers)
    Agent->>VN: python validate_numbers.py --ticker AMZN --stage C
    Note over VN: Header price, signal scores,<br/>financial figures, macro values<br/>cross-checked against source data
    alt Stage C FAIL
        VN-->>Agent: Report number mismatches
        Agent->>FS: Fix report HTML
        Agent->>VN: Re-run Stage C
    end
    VN-->>Agent: Stage C PASS

    Agent->>Audit: Phase 5: Post-Generation Audit
    Note over Audit: L1: Price consistency<br/>L2: Signal consistency<br/>L3: Financial sanity<br/>L4: Prediction integrity<br/>L5: Structure complete<br/>L6: Styling compliance<br/>L7: Macro data consistency

    alt All checks PASS
        Audit-->>Agent: READY TO PUBLISH
        Agent-->>User: Report generated + audit summary
    else Any check FAIL
        Audit-->>Agent: Auto-fix failures
        Agent->>Audit: Re-audit
        Audit-->>Agent: FIXED → READY TO PUBLISH
        Agent-->>User: Report generated (with fixes) + audit summary
    end
```

## Multi-Ticker Sequential Processing (CRITICAL)

When the user requests analysis for multiple tickers (e.g., "analyze AMZN, NVDA, and MSFT"),
all tickers are processed **sequentially** — each ticker completes the full pipeline
before the next ticker begins. Phases are **never interleaved** across tickers.

### Design Principles
- **Atomicity**: Each ticker's pipeline (Data → Engine → Pre-Gen Review → HTML → Save → Audit) runs as an atomic unit
- **Shared context**: Templates, CSS, `.instructions/` files, and macro data are loaded once and reused
- **Failure isolation**: A failure in ticker N does not block ticker N+1
- **Progress visibility**: Status is reported after each ticker completes

### Multi-Ticker Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Agent as Stock Analyst Agent
    participant AV as Alpha Vantage MCP
    participant PY as Python Scripts
    participant FS as File System

    User->>Agent: "analyze AMZN, NVDA, MSFT"
    Note over Agent: Parse ticker list: [AMZN, NVDA, MSFT]

    rect rgb(240, 249, 255)
        Note over Agent: ONE-TIME SETUP (shared across all tickers)
        Agent->>FS: Load templates/report-template.html (CSS)
        Agent->>FS: Load .instructions/* (specs)
        Agent->>FS: Load examples/HOOD-analysis.html (gold standard)
        Agent->>AV: Fetch macro data (CPI, FED_RATE, GDP, UNEMPLOYMENT)
        AV-->>Agent: Macro data cached for session
    end

    rect rgb(239, 246, 255)
        Note over Agent,PY: TICKER 1: AMZN (complete before next)
        Agent->>AV: Phase 1: Data Collection (AMZN) — 15 subject + peers
        AV-->>Agent: AMZN Data Bundle
        Agent->>FS: Write scripts/data/AMZN_bundle.json
        Agent->>PY: Phase 2: analyst_compute_engine.py --ticker AMZN
        PY-->>Agent: Exit 0 — 3 validated signal JSONs
        Note over Agent: Phase 3-5: HTML → Save → Audit
        Agent-->>User: ✅ AMZN complete (1/3). Starting NVDA...
    end

    rect rgb(245, 243, 255)
        Note over Agent,PY: TICKER 2: NVDA (complete before next)
        Agent->>AV: Phase 1: Data Collection (NVDA) — reuse macro data
        AV-->>Agent: NVDA Data Bundle
        Agent->>PY: Phase 2: analyst_compute_engine.py --ticker NVDA
        PY-->>Agent: Exit 0 — validated signals
        Note over Agent: Phase 3-5: HTML → Save → Audit
        Agent-->>User: ✅ NVDA complete (2/3). Starting MSFT...
    end

    rect rgb(255, 241, 242)
        Note over Agent,PY: TICKER 3: MSFT (final ticker)
        Agent->>AV: Phase 1: Data Collection (MSFT) — reuse macro data
        AV-->>Agent: MSFT Data Bundle
        Agent->>PY: Phase 2: analyst_compute_engine.py --ticker MSFT
        PY-->>Agent: Exit 0 — validated signals
        Note over Agent: Phase 3-5: HTML → Save → Audit
    end

    Agent-->>User: BATCH COMPLETE: 3/3 tickers processed
    Note over User: ✅ AMZN → reports/AMZN-analysis.html<br/>✅ NVDA → reports/NVDA-analysis.html<br/>✅ MSFT → reports/MSFT-analysis.html
```

### Multi-Ticker Flow (State Machine)

```mermaid
flowchart TB
    START([User: "analyze T1, T2, T3"]) --> PARSE["Parse ticker list"]
    PARSE --> SETUP["One-Time Setup<br/>Load templates + CSS + instructions<br/>Fetch macro data (CPI, FED, GDP, UNEMP)"]

    SETUP --> LOOP{"More tickers<br/>remaining?"}

    LOOP -->|Yes| PICK["Pick next ticker (Tn)"]
    PICK --> P1["Phase 1: Data Collection (Tn)<br/>15 subject + peers<br/>Reuse cached macro data"]
    P1 --> P1_OK{"Phase 1<br/>Success?"}
    P1_OK -->|Yes| WRITE["Write scripts/data/Tn_bundle.json"]
    P1_OK -->|No| FAIL["Log failure for Tn<br/>Skip to next ticker"]
    FAIL --> LOOP

    WRITE --> P1B["Phase 1b: Numerical Audit Stage A<br/>validate_numbers.py --stage A"]
    P1B --> P1B_OK{"Stage A<br/>PASS?"}
    P1B_OK -->|Yes| P2["Phase 2: analyst_compute_engine.py<br/>Phase 0: pre-flight (135 tests)<br/>validate inputs → compute → validate outputs"]
    P1B_OK -->|No| P1BFIX["Fix bundle data<br/>(max 2 retries)"]
    P1BFIX --> P1B
    P2 --> P2_OK{"Engine<br/>exit code?"}
    P2_OK -->|"0 (PASS)"| P2B["Phase 2b: Numerical Audit Stage B<br/>validate_numbers.py --stage B"]
    P2B --> P2B_OK{"Stage B<br/>PASS?"}
    P2B_OK -->|Yes| P3["Phase 3: Generate HTML<br/>20 sections, strict order<br/>Read signal JSONs directly"]
    P2B_OK -->|No| P2BFIX["Fix signals, re-run engine"]
    P2BFIX --> P2
    P2_OK -->|"1 (Input FAIL)"| REFETCH["Re-fetch missing data<br/>Update bundle (max 2 retries)"]
    REFETCH --> P2
    P2_OK -->|"2-3 (Error/Output FAIL)"| P2FIX["Review engine_report.json<br/>Fix data or report bug"]
    P2FIX --> P2

    P3 --> P4["Phase 4: Save<br/>reports/Tn-analysis.html"]
    P4 --> P4B["Phase 4b: Numerical Audit Stage C<br/>validate_numbers.py --stage C"]
    P4B --> P4B_OK{"Stage C<br/>PASS?"}
    P4B_OK -->|Yes| P5["Phase 5: Post-Gen Audit<br/>7 inline layers (L1-L7)"]
    P4B_OK -->|No| FIX3["Fix report numbers"]
    FIX3 --> P4B
    P5 --> P5_OK{"Audit<br/>PASS?"}
    P5_OK -->|Yes| REPORT["Report: ✅ Tn complete (n/total)"]
    P5_OK -->|No| FIX2["Auto-fix failures"]
    FIX2 --> P5
    REPORT --> LOOP

    LOOP -->|No| SUMMARY["Batch Summary<br/>✅ Completed tickers + file paths<br/>❌ Failed tickers + reasons"]
    SUMMARY --> DONE([Done])

    style START fill:#6366f1,color:#fff
    style SETUP fill:#f59e0b,color:#000
    style P1 fill:#0891b2,color:#fff
    style WRITE fill:#0891b2,color:#fff
    style P1B fill:#d97706,color:#fff
    style P2 fill:#059669,color:#fff
    style P2B fill:#d97706,color:#fff
    style P3 fill:#7c3aed,color:#fff
    style P4 fill:#16a34a,color:#fff
    style P4B fill:#d97706,color:#fff
    style P5 fill:#ef4444,color:#fff
    style FAIL fill:#dc2626,color:#fff
    style REPORT fill:#22c55e,color:#fff
    style SUMMARY fill:#1b2a4a,color:#fff
    style DONE fill:#6366f1,color:#fff
```

### Shared vs Per-Ticker Data

| Data Type | Scope | Fetch Strategy |
|-----------|-------|----------------|
| Templates, CSS, `.instructions/` | Session-wide | Load once at setup, reuse for all tickers |
| Python scripts (`scripts/*.py`) | Session-wide | Already on disk, reused for all tickers |
| Macro data (CPI, FED_RATE, GDP, UNEMPLOYMENT) | Market-wide | Fetch once at setup, cache for session |
| Subject data (15 endpoints) | Per-ticker | Fetch fresh for each ticker |
| Peer data (3-5 competitors) | Per-ticker | Fetch fresh — peers differ per ticker |
| Data bundle JSON (`scripts/data/`) | Per-ticker | Written fresh — overwritten on re-run |
| Signal computation (analyst_compute_engine.py) | Per-ticker | Engine runs fresh per ticker |
| Numerical audit (`validate_numbers.py`) | Per-ticker | Runs 3 stages (A/B/C) per ticker |
| Validation reports | Per-ticker | Generated fresh by engine |
| HTML report | Per-ticker | Generate fresh — each ticker has unique content |

### Failure Handling

- **MCP rate limit**: Log which ticker failed, skip it, continue with next
- **Missing data**: If a critical endpoint returns no data, log and skip the ticker
- **Audit failure after retries**: Save the report but mark it in the summary as "NEEDS REVIEW"
- **All failures logged**: Final batch summary includes every failure with reason
- **No cascading failures**: One ticker's failure never affects another ticker's processing

## Test & Verification Architecture

### Test Framework Overview

All testing flows through a single entry point: `scripts/run_tests.py`. There are **no standalone test scripts** — every test mode is a flag on the unified runner.

```mermaid
graph TB
    subgraph TestRunner["run_tests.py — Unified Test System"]
        direction TB
        CLI["CLI Entry Point<br/>──────────────────<br/>--suite (unit/contract/integration/quick/all)<br/>--live TICKER [--apikey KEY]<br/>--golden TICKER|all<br/>--list / --verbose / --json"]

        subgraph Suites["Automated Test Suites (183 tests, <0.5s)"]
            direction LR
            UT["Unit Tests (113)<br/>──────────────────<br/>test_unit_short_term.py (26)<br/>test_unit_ccrlo.py (22)<br/>test_unit_simulation.py (20)<br/>test_unit_tags.py (45)"]
            CT["Contract Tests (22)<br/>──────────────────<br/>test_contracts.py<br/>Schema compliance<br/>+ Golden regression"]
            IT["Integration Tests (12)<br/>──────────────────<br/>test_integration.py<br/>Full pipeline E2E<br/>Cross-module consistency"]
        end

        subgraph LiveTest["Live Pipeline Test (--live)"]
            LT2["Fetch or load bundle<br/>→ Input validation<br/>→ Compute engine<br/>→ Output validation<br/>→ Numerical audit"]
        end

        subgraph GoldenMgr["Golden Reference Manager (--golden)"]
            GM["Snapshot current outputs<br/>as regression baselines<br/>for TEST, STRESS,<br/>AMZN, HOOD, MSFT"]
        end
    end

    CLI --> Suites
    CLI --> LiveTest
    CLI --> GoldenMgr

    subgraph Fixtures["Test Fixtures (tests/fixtures.py)"]
        MB["MINIMAL_BUNDLE<br/>Healthy company, ticker=TEST"]
        DB["DISTRESSED_BUNDLE<br/>High beta, recent IPO, oversold<br/>ticker=STRESS"]
    end

    subgraph Golden["Golden References (tests/golden/)"]
        GF["15 files: 5 tickers × 3 signals<br/>TEST, STRESS (from fixtures)<br/>AMZN, HOOD, MSFT (from bundles)"]
    end

    Fixtures --> UT
    Fixtures --> CT
    Fixtures --> IT
    Golden --> CT

    subgraph Outputs["Test Outputs"]
        JR["scripts/output/test_results_latest.json<br/>Always updated after every run"]
    end

    Suites --> JR

    style CLI fill:#0ea5e9,color:#fff
    style UT fill:#3b82f6,color:#fff
    style CT fill:#8b5cf6,color:#fff
    style IT fill:#16a34a,color:#fff
    style LT2 fill:#f59e0b,color:#000
    style GM fill:#ec4899,color:#fff
    style MB fill:#f0fdf4,stroke:#bbf7d0
    style DB fill:#fff1f2,stroke:#fecdd3
    style GF fill:#faf5ff,stroke:#e9d5ff
    style JR fill:#f0f9ff,stroke:#bae6fd
```

### Change Verification Protocol

Every agent (stock-analyst, test-engineer, or default Copilot) must follow this protocol
whenever modifying any system file in `scripts/`. This is enforced via `copilot-instructions.md`
(auto-loaded for every conversation).

```mermaid
flowchart TB
    CHANGE([System file modified]) --> IDENTIFY["Step 1: PROPAGATE<br/>Identify all dependent files"]

    IDENTIFY --> DEP{"What changed?"}

    DEP -->|"Compute script<br/>(formula/logic)"| P1["Update:<br/>• Golden references<br/>• Test fixtures (if schema)<br/>• signal-contracts.md (if schema)"]
    DEP -->|"Validation rule"| P2["Update:<br/>• Validator script<br/>• Test expectations"]
    DEP -->|"Signal output field<br/>(renamed/added/removed)"| P3["Update:<br/>• compute_*.py<br/>• validate_outputs.py<br/>• validate_numbers.py<br/>• signal-contracts.md<br/>• test fixtures<br/>• contract tests<br/>• agent.md references"]
    DEP -->|"Data bundle schema"| P4["Update:<br/>• validate_inputs.py<br/>• test fixtures<br/>• data-collection skill"]

    P1 --> TEST
    P2 --> TEST
    P3 --> TEST
    P4 --> TEST

    TEST["Step 2: TEST<br/>python scripts/run_tests.py --suite quick<br/>python scripts/run_tests.py --suite all"]

    TEST --> RESULT{"183/183<br/>pass?"}

    RESULT -->|Yes| CONFIRM["Step 3: CONFIRM<br/>Report '183/183 tests pass'<br/>Change is complete ✅"]
    RESULT -->|"No — intentional change"| GOLDEN["Update golden refs:<br/>python scripts/run_tests.py --golden all<br/>Re-run --suite all"]
    RESULT -->|"No — bug"| FIXBUG["Fix the source code<br/>Re-run tests"]

    GOLDEN --> RESULT
    FIXBUG --> RESULT

    style CHANGE fill:#6366f1,color:#fff
    style IDENTIFY fill:#f59e0b,color:#000
    style TEST fill:#0ea5e9,color:#fff
    style CONFIRM fill:#16a34a,color:#fff
    style GOLDEN fill:#8b5cf6,color:#fff
    style FIXBUG fill:#ef4444,color:#fff
```

### Change Impact Matrix

| File Changed | Must Also Update | Test Command |
|---|---|---|
| `compute_short_term.py` | golden refs, fixtures if schema changed | `--suite all` |
| `compute_ccrlo.py` | golden refs, fixtures if schema changed | `--suite all` |
| `compute_simulation.py` | golden refs, fixtures if schema changed | `--suite all` |
| `validate_inputs.py` | fixtures if new checks added | `--suite integration` |
| `validate_outputs.py` | contract tests if new checks | `--suite integration` |
| `validate_numbers.py` | — | `--live AMZN` |
| `analyst_compute_engine.py` | — | `--suite integration` |
| `signal-contracts.md` | validate_outputs.py, contract tests | `--suite contract` |
| `tests/fixtures.py` | golden refs | `--suite all` + `--golden all` |
| Data bundle schema | validate_inputs.py, fixtures, data-collection skill | `--suite all` |

### Test Categories & What They Catch

```mermaid
graph LR
    subgraph UnitTests["Unit Tests (113)"]
        U1["Function-level correctness"]
        U2["Edge cases & boundaries"]
        U3["Score range validation"]
    end

    subgraph ContractTests["Contract Tests (22)"]
        C1["Output schema structure"]
        C2["Required key presence"]
        C3["Golden regression comparison"]
    end

    subgraph IntegrationTests["Integration Tests (12)"]
        I1["Full pipeline E2E"]
        I2["Cross-module consistency"]
        I3["Real bundle compatibility"]
    end

    subgraph Catches["What They Catch"]
        B1["Logic bugs"]
        B2["Schema drift"]
        B3["Unintended value changes"]
        B4["Cross-module breaks"]
        B5["Data format issues"]
    end

    U1 --> B1
    U2 --> B1
    C1 --> B2
    C3 --> B3
    I1 --> B4
    I3 --> B5

    style U1 fill:#3b82f6,color:#fff
    style U2 fill:#3b82f6,color:#fff
    style U3 fill:#3b82f6,color:#fff
    style C1 fill:#8b5cf6,color:#fff
    style C2 fill:#8b5cf6,color:#fff
    style C3 fill:#8b5cf6,color:#fff
    style I1 fill:#16a34a,color:#fff
    style I2 fill:#16a34a,color:#fff
    style I3 fill:#16a34a,color:#fff
    style B1 fill:#ef4444,color:#fff
    style B2 fill:#ef4444,color:#fff
    style B3 fill:#ef4444,color:#fff
    style B4 fill:#ef4444,color:#fff
    style B5 fill:#ef4444,color:#fff
```

### Agent Roles

| Agent | Role | Trigger Examples |
|-------|------|-----------------|
| **@stock-analyst** | Generates reports, computes signals, collects data. Must run `--suite all` after modifying any system file. | "analyze AMZN", "compute signals", "fix report" |
| **@test-engineer** | Tests system, diagnoses failures, manages golden refs. Enforces Change Verification Protocol. | "run tests", "did my changes break anything?", "update golden refs" |
