---
plan_type: "layerable_extension_plan"
plan_id: "extension_proactive_intelligence"
name: "Proactive Intelligence & Anomaly Detection Extension"
parent_master_plan: ".nb/plan/personal_os/concise.md"
tier_mapping:
  tier_2: "Domain Rules & Contracts (.nb/context/contracts/, context/rules/)"
  tier_3: "Specialist Subagents & Workflows (.nb/agentic/custom/agents/, agentic/custom/workflows/)"
model_tiering_policy:
  provider_agnostic: true
  tier_a_model: "claude-3-7-sonnet / pro"
  tier_b_model: "claude-3-5-haiku / flash"
  tier_c_model: "deterministic local statistics (ndarray / statrs)"
---

# Layerable Extension Plan: Proactive Intelligence & Anomaly Detection

### Executive Overview
The **Proactive Intelligence Extension** augments Personal OS with autonomous sensing, statistical baseline learning, and proactive anomaly detection across all eight core life pillars. Rather than passively waiting for user queries, the engine continuously calculates behavioral baselines, identifies statistically significant deviations, and schedules non-intrusive interventions (nudges, alerts, and suggestions) to prevent burnout, protect habits, curb overspending, and maintain key relationships.

---

## 1. Domain-Specific Quad-Space Mapping

```
.
├── context/
│   ├── contracts/
│   │   └── proactive_intelligence_contracts.yaml # Wire schemas for anomalies and nudges
│   └── rules/
│       └── proactive_ethics_rules.md             # Privacy, throttling, and anti-nagging invariants
├── agentic/
│   ├── custom/agents/
│   │   └── agent_proactive_sentinel.yaml         # Autonomous pattern monitor & intervention agent
│   └── custom/workflows/
│       ├── wf_proactive_daily_eval.yaml          # Scheduled daily baseline recalculation
│       └── wf_spending_anomaly_alert.yaml        # Real-time transaction outlier trigger
├── workplace/
│   └── modules/
│       ├── pos_proactive/                        # Core proactive engine and intervention router
│       ├── pos_anomaly/                          # Statistical algorithms (Z-score, IQR, EMA)
│       └── pos_baseline/                         # Rolling 90-day baseline aggregator
└── user/
    └── hitl/
        └── proactive_feedback_queue.md           # User dismissals, snoozes, and false-positive logs
```

---

## 2. Statistical Anomaly Algorithms & Schema

### 2.1. Detection Algorithms
1. **Z-Score Normalization**:
   $$Z = \frac{x - \mu}{\sigma}$$
   Triggered when $|Z| > 2.0$ (representing 95.4% confidence deviation from rolling 90-day mean $\mu$).
2. **Interquartile Range (IQR) Fence**:
   $$\text{Outlier} = x > Q_3 + 1.5 \cdot \text{IQR} \quad \text{or} \quad x < Q_1 - 1.5 \cdot \text{IQR}$$
   Used for skewed distributions (such as transaction amounts and meeting durations).
3. **Exponential Moving Average (EMA) Velocity**:
   $$\text{EMA}_t = \alpha \cdot x_t + (1 - \alpha) \cdot \text{EMA}_{t-1}$$
   Detects velocity shifts in habit completion and project sprint burn-down rates.

### 2.2. SQLite Baseline Storage Schema
```sql
CREATE TABLE IF NOT EXISTS baseline_stats (
    pillar TEXT NOT NULL,
    metric_key TEXT NOT NULL,
    window_days INTEGER NOT NULL DEFAULT 90,
    sample_count INTEGER NOT NULL,
    mean REAL NOT NULL,
    std_dev REAL NOT NULL,
    p25 REAL NOT NULL,
    p50 REAL NOT NULL,
    p75 REAL NOT NULL,
    p95 REAL NOT NULL,
    last_computed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (pillar, metric_key)
);

CREATE TABLE IF NOT EXISTS proactive_insights (
    id TEXT PRIMARY KEY,
    pillar TEXT NOT NULL,
    insight_type TEXT NOT NULL CHECK (insight_type IN ('spending_spike', 'habit_risk', 'social_gap', 'burnout_warning', 'project_slip')),
    severity TEXT NOT NULL CHECK (severity IN ('high', 'medium', 'low', 'info')),
    confidence_score REAL NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    suggested_action JSON,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'dismissed', 'snoozed', 'accepted')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snoozed_until DATETIME
);
```

---

## 3. Wire Contracts & Anti-Nagging Invariants

### 3.1. Non-Negotiable Invariants (`context/rules/proactive_ethics_rules.md`)
1. **Anti-Nagging Rate Limit**: Maximum 2 high-priority alerts per day; maximum 5 total notifications per 24-hour rolling period.
2. **Context-Aware Suppression**: Zero sound/vibration alerts during scheduled focus blocks (`pos_activities`) or sleep hours (10:00 PM – 07:00 AM).
3. **Local Mathematical Evaluation**: All baseline modeling and anomaly detection execute deterministically in safe Rust on the local CPU; zero raw telemetry is sent to cloud LLMs.
4. **Immediate User Sovereignty**: Every insight must provide one-click `[Dismiss]` and `[Snooze]` actions; recurring dismissals (> 2 times) automatically recalibrate anomaly thresholds upward.

---

## 4. Verification & Testing Protocol

```bash
# 1. Run statistical baseline unit tests
cargo test -p pos_anomaly --lib

# 2. Test anomaly detection under simulated synthetic variance
cargo test -p pos_proactive --test synthetic_spending_spike_test

# 3. Verify anti-nagging rate limiter invariants
cargo test -p pos_proactive --test rate_limiter_invariants_test
```
