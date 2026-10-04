# Master Plan: Parent Master Context Engineering Framework (Free Community Edition)

**Plan ID**: `master_parent_free_community`  
**Capability Rating**: `Free Community Tier`  
**Version**: `7.5.0`  

## Overview

The **Free Community Edition** of the Parent Master Plan delivers the core deterministic, tamper-evident, and token-efficient platform engines to individual developers and open-source teams with zero external service dependencies.

## Quick Links

- **Concise Plan**: [concise.md](./concise.md) — Compact community specification (~360 lines)
- **Detailed Plan**: [detailed.md](./detailed.md) — Extended implementation guide & IDE integration reference (~150 lines)
- **Version Manifest**: [MANIFEST.yaml](./MANIFEST.yaml) — Cryptographic SHA-256 version ledger

## Key Features

- **Single Canonical Binary**: Zero symlink confusion; `.nb/bin/percipience` is the sole gatekeeper.
- **Embedded Free Tier Assets**: Platform binaries, configs, and CI/CD workflows packaged in IDE plugin JARs.
- **AST Token Reduction**: 60%–80% context compression via Tree-Sitter AST skeletonization.
- **SHA-256 Merkle Ledger**: Local tamper-evident audit chain in `context_ledger.yaml`.
- **Basic Autonomous CI/CD**: Single-attempt bounded self-repair and contract verification.

## Success Criteria

- Clean platform bootstrapping from IDE startup notifications.
- 100% passing test suites on community tier verification harnesses.
- Fully transparent, unsealed plaintext execution with complete local governance.
