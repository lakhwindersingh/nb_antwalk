---
plan_type: "layerable_extension_plan"
plan_id: "extension_native_apple_siri"
name: "Native Apple Siri Integration Extension Plan"
parent_plan: ".nb/plan/personal_os/concise.md"
tier_mapping:
  tier_2: "Siri Wire Contracts & Rules (.nb/context/contracts/native_siri_*, context/rules/native_siri_*)"
  tier_3: "iOS Sync Agent & Workflows (.nb/agentic/custom/agents/agent_ios_*, agentic/custom/workflows/wf_*_siri)"
model_tiering_policy:
  provider_agnostic: true
  tier_a_model: "claude-3-7-sonnet / pro"
  tier_b_model: "claude-3-5-haiku / flash"
---

# Native Apple Apps with Siri: Executive Summary

### Executive Overview
Native iOS/macOS companion apps that integrate Personal OS with Apple's ecosystem through **SiriKit App Intents, Announce Notifications, Shortcuts, Widgets, and Live Activities**. Enables voice control, proactive suggestions, and system-level integration without custom wake word detection—leveraging Apple's native Siri infrastructure.

---

## 1. System Topology



---

## 2. Key Capabilities
- **E-SIRI-01 (App Intents)**: Native Siri invocation for thought capture, daily briefings, and interaction logging.
- **E-SIRI-02 (UniFFI Bridge)**: High-speed POSIX domain socket communication with Personal OS daemon.
- **E-SIRI-03 (Live Activities)**: Real-time Dynamic Island timers and recording status widgets.
- **E-SIRI-04 (Shortcuts)**: Parameterized system automation actions exposing Personal OS query tools.

---

## 3. Privacy & Security Invariants
1. **Keychain Secret Storage**: Encrypted credential storage via Apple Keychain Secure Enclave.
2. **Direct POSIX Socket Transport**: Zero public network ports open on localhost.
3. **Apple Privacy Compliance**: Strict adherence to App Store Review guidelines for background execution.
