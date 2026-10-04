# Personal OS & Percipience Context Engineering Plans

Welcome to the **Percipience Plan Space** (`.nb/plan/`). This directory houses the governance, architecture, and extension specifications for **Personal OS** and the underlying **Parent Master Context Engineering Framework**.

> [!IMPORTANT]
> **Plan Lineage & Implementation Index**: For the authoritative execution graph, topological implementation order (Lean MVP 8-Week Track vs. Full Enterprise 24-Week Track), prerequisite/successor dependencies, and platform invariant mappings, consult [**`PLAN_LINEAGE_AND_INDEX.md`**](./PLAN_LINEAGE_AND_INDEX.md).

---

## 🧭 Plan Directory Navigation

```
.nb/plan/
├── PLAN_LINEAGE_AND_INDEX.md        # 🌟 Master Plan Lineage, Topological Order & Dependency Index
├── master/                      # Framework Orchestration Foundation
│   ├── parent-master-plan/      # Complete 36-capability master plan (v7.5.0)
│   └── parent-master-free-plan/ # Community edition framework specification
├── personal_os/                 # Personal OS Core Domain Architecture
│   ├── MANIFEST.yaml            # Machine-readable plan metadata & version hash ledger
│   ├── README.md                # Quick navigation and architecture overview
│   ├── concise.md               # Concise layerable domain specification (~170 lines)
│   ├── detailed.md              # Comprehensive blueprint (~430 lines)
│   └── IMPROVEMENTS_SUMMARY.md  # Record of core plan improvements
├── architecture/                # Architecture Gaps & Hardening Specifications
│   ├── GAPS_COMPLETE.md         # Master 12-gap analysis matrix & resolution roadmap
│   ├── crdt_conflict_resolution.md # GAP-001: Yrs CRDT multi-device sync
│   ├── storage_write_batching.md   # GAP-002: MPSC write batching coordinator
│   ├── embedding_versioning.md     # GAP-003: Vector embedding versioning & migration
│   ├── pii_anonymization.md        # GAP-004: Dual-pass NER & PII anonymization
│   └── saga_workflow_durability.md # GAP-005: Durable saga workflow execution
├── extensions/                  # Modular Subsystem Extensions
│   ├── README.md                # Extension index & priority matrix (P0-P3)
│   ├── email_triage/            # P0: Smart inbox, IMAP sync & entity extraction
│   ├── voice_interface/         # P0: Local Whisper audio pipeline & speech capture
│   ├── native_apple_siri/       # P0: iOS/macOS SiriKit App Intents & Live Activities
│   ├── native_android/          # P0: Android/Wear OS Google Assistant & Glance widgets
│   ├── proactive_intelligence/  # P0: Baseline learning & anomaly detection
│   ├── meeting_intelligence/    # P1: Meeting auto-join, diarization & summaries
│   └── thought_to_project/      # P0: Thought-to-Project Autonomous Plan & CI/CD Pipeline
├── templates/                   # Standard Domain & Extension Templates
│   └── custom_domain_layer_template.md # Layerable domain engineering template
├── COMPLETE_SUMMARY.md          # Complete documentation summary & logical Mermaid diagrams
├── INTERACTION_POINTS.md        # Master interaction mechanisms & loose ends analysis
├── NATIVE_SIRI_SUMMARY.md       # Summary of Native Apple Siri integration
└── USE_CASES_AND_MARKET_VALUE.md # Commercial use cases, ROI models & market valuation
```

---

## 🏛️ Layered Context Precedence Hierarchy

Plans in this workspace adhere to the **3-Tier Precedence Hierarchy**:
- **Tier 1 (Base Platform Invariants)**: Non-overridable platform invariants in `.nb/context/invariants/`, [.nb/context/rules/personal_os_invariants.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/context/rules/personal_os_invariants.md), and `.nb/plan/master/`.
- **Tier 2 (Enterprise & Domain Wire Contracts)**: Domain wire contracts in `.nb/context/contracts/` and rules in `.nb/context/rules/`.
- **Tier 3 (Domain Specifications & Extensions)**: Specialist agent manifests in `.nb/agentic/custom/` and plans in `.nb/plan/personal_os/` & `.nb/plan/extensions/`.

---

## 💼 Commercialization & Operationalization

- **Use Cases & Market Valuation**: Detailed in [USE_CASES_AND_MARKET_VALUE.md](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/plan/USE_CASES_AND_MARKET_VALUE.md), analyzing 5 core operational use cases across DevTools, Executive Life OS, Regulated Legal/Medical Knowledge Vaults, Personal FinOps, and Family Office Sovereign Clouds.
- **Economic Model**: Grounded in [.nb/config/billing_plans.yaml](file:///Users/lakhwinder/RustroverProjects/nb_antwalk/.nb/config/billing_plans.yaml) across Free Community ($0), Team ($1,499/mo), Business ($4,499/mo), and Enterprise Dedicated ($9,999/mo) tiers with a 15% Token FinOps revenue-share model.
