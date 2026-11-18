# 📊 Percipience Master Capability Cross-Reference Matrix

> **Generated Automatically**: Certified via `.nb/plan/scripts/generate_capability_index.py`  
> **Total Plans Tracked**: 10  

---

## 1. Master Plan Capabilities & Governance Matrix

| Plan ID | Layer | Stage | Parity ($S_{SP}$) | Production Ready | Capabilities Count |
| :--- | :---: | :---: | :---: | :---: | :---: |
| [`master_parent_framework`](./master/parent-master-plan) | `master` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 8 |
| [`master_parent_free_community`](./master/parent-master-free-plan) | `master` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 5 |
| [`domain_personal_os`](./personal_os) | `domain` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 17 |
| [`extension_email_triage`](./extensions/email_triage) | `extensions` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 8 |
| [`extension_meeting_intelligence`](./extensions/meeting_intelligence) | `extensions` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 8 |
| [`extension_native_android`](./extensions/native_android) | `extensions` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 4 |
| [`extension_native_apple_siri`](./extensions/native_apple_siri) | `extensions` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 4 |
| [`extension_proactive_intelligence`](./extensions/proactive_intelligence) | `extensions` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 6 |
| [`extension_thought_to_project`](./extensions/thought_to_project) | `extensions` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 8 |
| [`extension_voice_interface`](./extensions/voice_interface) | `extensions` | `IMPLEMENTATION_READY` | `0.985` | ✅ Ready | 6 |

---

## 2. Detailed Capability Inventory by Plan

### `master_parent_framework`: Parent Master Context Engineering Framework
- **Location**: [master/parent-master-plan](./master/parent-master-plan)
- **Layer**: `master`
- **Requires**: *None (Root)*
- **Key Capabilities**:
  - Autonomous Operations on MVS Inputs (CAP-01)
  - Context Poisoning Detection & Rollback (CAP-02)
  - Context Compression & Token FinOps (CAP-03)
  - Dynamic Multi-Model Cascading (CAP-04)
  - Git Worktree Workspace Isolation (CAP-05)
  - Cryptographic Merkle State Ledger (CAP-08)
  - Autonomous Closed-Loop CI/CD Triad (CAP-16)
  - 3-Tier Layered Context Precedence Hierarchy (CAP-20)

### `master_parent_free_community`: Parent Master Context Engineering Framework (Free Community Edition)
- **Location**: [master/parent-master-free-plan](./master/parent-master-free-plan)
- **Layer**: `master`
- **Requires**: `master/parent-master-plan/concise.md`
- **Key Capabilities**:
  - Single Canonical Gatekeeper Binary (.nb/bin/percipience)
  - Embedded Free Tier Plugin Assets & Startup Notification
  - Tree-Sitter AST Token Reduction (60-80%)
  - SHA-256 Merkle Ledger State Chaining
  - Basic Autonomous CI/CD Self-Repair Loop

### `domain_personal_os`: Personal OS (Rust-based Agentic Life Operating System)
- **Location**: [personal_os](./personal_os)
- **Layer**: `domain`
- **Requires**: `master_parent_framework`
- **Key Capabilities**:
  - {'P-OS-01': 'Multi-Workspace Project & Git Worktree Lifecycle Engine'}
  - {'P-OS-02': 'Content-Addressable Semantic File Indexer & Watcher Daemon'}
  - {'P-OS-03': 'Zettelkasten Knowledge Graph & Associative Thought Capture'}
  - {'P-OS-04': 'Bi-Directional Activity & Calendar Schedule Orchestrator'}
  - {'P-OS-05': 'Declarative Async Workflow DAG & Background Routine Engine'}
  - {'P-OS-06': 'Zero-Knowledge Encrypted Vault & Agent Secret Brokerage'}
  - {'P-OS-07': 'Relationship & Communication Interaction CRM Engine'}
  - {'P-OS-08': 'Double-Entry Financial Ingestion & Subscription Auditor'}
  - {'P-OS-09': 'Local High-Throughput SQLite-WAL + Tantivy Hybrid Storage'}
  - {'P-OS-10': 'Model Context Protocol (MCP) Server & Client Federation'}
  - {'P-OS-11': 'Zero-Leak Redaction & In-Memory Enclave Secret Leasing'}
  - {'P-OS-12': 'Autonomous Morning Brief & Evening Reflection Synthesizer'}
  - {'P-OS-13': 'Meta-Orchestrator Request Routing & Classification Engine'}
  - {'P-OS-14': 'Durable Saga Workflow Execution & Checkpointing Engine'}
  - {'P-OS-15': 'Yrs CRDT Multi-Device Peer Synchronization Engine'}
  - {'P-OS-16': 'BIP-39 Vault Disaster Recovery & M-of-N Quorum Derivation'}
  - {'P-OS-17': 'Pragmatic 3-Crate Modular Monolith & Lean Architecture Engine'}

### `extension_email_triage`: AI-Powered Email Triage & Smart Inbox
- **Location**: [extensions/email_triage](./extensions/email_triage)
- **Layer**: `extensions`
- **Requires**: `domain_personal_os`, `pos_interactions`, `pos_projects`, `pos_vault`
- **Key Capabilities**:
  - {'E-EMAIL-01': 'IMAP/Gmail API Email Fetching & Sync'}
  - {'E-EMAIL-02': 'Intelligent Category Classification (Action Required, FYI, Newsletter, Receipt, Spam)'}
  - {'E-EMAIL-03': 'Email Summarization & Key Point Extraction'}
  - {'E-EMAIL-04': 'Action Item & Task Extraction'}
  - {'E-EMAIL-05': 'Meeting Invite Auto-Parsing to Calendar'}
  - {'E-EMAIL-06': 'Contact Auto-Extraction to CRM'}
  - {'E-EMAIL-07': 'Receipt Detection & Financial Ingestion'}
  - {'E-EMAIL-08': 'Smart Reply Draft Generation'}

### `extension_meeting_intelligence`: Meeting Intelligence & Auto-Transcription Extension
- **Location**: [extensions/meeting_intelligence](./extensions/meeting_intelligence)
- **Layer**: `extensions`
- **Requires**: `domain_personal_os`
- **Key Capabilities**:
  - {'E-MEET-01': 'Calendar Auto-Join Bot (Zoom / Google Meet / Microsoft Teams)'}
  - {'E-MEET-02': 'Participant Consent & Multi-Channel Audio Recording'}
  - {'E-MEET-03': 'Local Whisper Speech-to-Text with Word Timestamps'}
  - {'E-MEET-04': 'Acoustic Speaker Diarization & Voiceprint Clustering'}
  - {'E-MEET-05': 'Autonomous Action Item & Task Extraction'}
  - {'E-MEET-06': 'Structured Decision Synthesis & Markdown Executive Briefs'}
  - {'E-MEET-07': 'Contextual Pre-Meeting Dossier Generation'}
  - {'E-MEET-08': 'One-Click Post-Meeting Email & Follow-Up Drafting'}

### `extension_native_android`: Native Android Apps with Google Assistant & Gemini Nano Integration
- **Location**: [extensions/native_android](./extensions/native_android)
- **Layer**: `extensions`
- **Requires**: `personal_os`, `pos_core`, `pos_server`
- **Key Capabilities**:
  - Native Android Apps with Google Assistant & Gemini Nano Integration Architecture
  - Autonomous EXTENSIONS Derivation & Execution Engine
  - Cryptographic State Ledger Verification
  - Zero-Drift Invariant Gatekeeper Compliance

### `extension_native_apple_siri`: Native Apple Apps with Siri Integration
- **Location**: [extensions/native_apple_siri](./extensions/native_apple_siri)
- **Layer**: `extensions`
- **Requires**: `personal_os`
- **Key Capabilities**:
  - Native Apple Apps with Siri Integration Architecture
  - Autonomous EXTENSIONS Derivation & Execution Engine
  - Cryptographic State Ledger Verification
  - Zero-Drift Invariant Gatekeeper Compliance

### `extension_proactive_intelligence`: Proactive Intelligence & Anomaly Detection Extension
- **Location**: [extensions/proactive_intelligence](./extensions/proactive_intelligence)
- **Layer**: `extensions`
- **Requires**: `domain_personal_os`
- **Key Capabilities**:
  - {'E-PROACT-01': 'Baseline Statistical Learning Engine (Rolling 90-day window per pillar)'}
  - {'E-PROACT-02': 'Financial Spending Anomaly Detector (Z-score & IQR outlier analysis)'}
  - {'E-PROACT-03': 'Habit Streak Protection & Break Risk Predictor'}
  - {'E-PROACT-04': 'Relationship Maintenance & Social Cadence Sentinel'}
  - {'E-PROACT-05': 'Work-Life Balance & Cognitive Burnout Monitor'}
  - {'E-PROACT-06': 'Context-Aware Smart Nudges & Optimal Delivery Scheduler'}

### `extension_thought_to_project`: Thought-to-Project Autonomous Plan Pipeline Extension
- **Location**: [extensions/thought_to_project](./extensions/thought_to_project)
- **Layer**: `extensions`
- **Requires**: `domain_personal_os`, `master_parent_framework`
- **Key Capabilities**:
  - {'E-THOUGHT-01': 'Thought AST Parsing & Actionability Evaluation (CommonMark AST to semantic readiness score)'}
  - {'E-THOUGHT-02': 'Autonomous MVS Input Derivation (Normalizes unstructured notes into formal specifications)'}
  - {'E-THOUGHT-03': 'Ambiguity Entropy Analysis & HITL Clarification RFCs (Resolves vague requirements)'}
  - {'E-THOUGHT-04': 'Domain Layer Plan Generator (Auto-generates custom domain layer plans per template)'}
  - {'E-THOUGHT-05': 'Petgraph Task DAG Decomposition (Compiles plan into directed acyclic dependency graphs)'}
  - {'E-THOUGHT-06': 'Ephemeral Git Worktree Provisioning (Isolates subagents in branch sandboxes via git2/worktree_engine)'}
  - {'E-THOUGHT-07': 'Autonomous CI/CD Triad Execution Bridge (Closed-loop TDD self-healing and Merkle audit)'}
  - {'E-THOUGHT-08': 'Bidirectional State Synchronization & Knowledge Closure (Backlinks commits/PRs to original thought)'}

### `extension_voice_interface`: Voice Interface & Dictation System
- **Location**: [extensions/voice_interface](./extensions/voice_interface)
- **Layer**: `extensions`
- **Requires**: `domain_personal_os`, `pos_thoughts`, `pos_activities`
- **Key Capabilities**:
  - {'E-VOICE-01': 'Local Speech-to-Text (Whisper)'}
  - {'E-VOICE-02': 'Wake Word Detection ("Hey Kiro")'}
  - {'E-VOICE-03': 'Voice Command Parsing & Intent Recognition'}
  - {'E-VOICE-04': 'Voice Thought Capture & Journaling'}
  - {'E-VOICE-05': 'Natural Language Query Interface'}
  - {'E-VOICE-06': 'Text-to-Speech Response (Optional)'}

