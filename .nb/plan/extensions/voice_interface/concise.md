---
plan_type: "layerable_extension_plan"
plan_id: "extension_voice_interface"
name: "Voice Interface & Dictation Extension Plan"
parent_plan: ".nb/plan/personal_os/concise.md"
tier_mapping:
  tier_2: "Voice Wire Contracts & Rules (.nb/context/contracts/voice_*, context/rules/voice_*)"
  tier_3: "Voice Agents & Workflows (.nb/agentic/custom/agents/agent_voice_*, agentic/custom/workflows/wf_voice_*)"
model_tiering_policy:
  provider_agnostic: true
  tier_a_model: "claude-3-7-sonnet / pro"
  tier_b_model: "claude-3-5-haiku / flash"
---

# Voice Interface & Dictation: Executive Brief

### Executive Overview
This extension enables hands-free interaction with Personal OS through natural speech, using local Whisper-based transcription for complete privacy. Voice commands reduce friction for thought capture (3 seconds vs 30 seconds typing), enable accessibility, and support on-the-go productivity.

---

## 1. Extension Topology & Space Mapping



---

## 2. Key Capabilities
- **E-VOX-01 (Streaming VAD)**: Sub-5ms frame-level speech detection via quantized Silero neural net.
- **E-VOX-02 (Speech-to-Text)**: Real-time local Whisper streaming with <300ms latency.
- **E-VOX-03 (Neural TTS)**: On-device natural speech synthesis via ONNX Piper runtime.
- **E-VOX-04 (Intent Dispatch)**: Direct grammar-constrained intent mapping to CLI commands.

---

## 3. Privacy & Offline Invariants
1. **Local-First Boundary**: Audio streams processed 100% on-device; zero remote network leakage.
2. **Volatile In-Memory Ring-Buffer**: Audio frames zeroized immediately upon utterance commit.
3. **Physical Mute Indication**: Visual status beacon active whenever microphone is open.
