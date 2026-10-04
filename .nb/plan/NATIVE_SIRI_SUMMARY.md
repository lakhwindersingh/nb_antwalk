# Native Apple Siri Integration - Specification Summary

**Extension ID**: native_apple_siri  
**Status**: Specification Complete  
**Priority**: P0 (Core Extension)  
**Created**: 2024-10-04  
**Files**: 8 core files, ~2,800 lines

---

## Executive Summary

Complete specification for native iOS/macOS integration using Apple's SiriKit framework, Announce Notifications, Widgets, and Live Activities. Enables hands-free interaction, proactive intelligence, and deep ecosystem integration while maintaining privacy through on-device processing and local-first architecture.

**Key Distinction**: Unlike the Whisper-based Voice Interface extension (custom wake word detection), this extension uses Apple's native SiriKit App Intents infrastructure for first-class iOS/macOS integration.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Apple Ecosystem Layer                     │
│  Siri · Shortcuts · Widgets · Live Activities · Spotlight   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   App Intents Framework                      │
│  CaptureThought · QueryAgenda · LogHabit · CreateTask       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    Local-First Layer                         │
│         Core Data · SwiftData · Keychain Services            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Background Sync Layer                       │
│      agent_ios_sync_coordinator · BGTaskScheduler           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Personal OS Backend                         │
│               HTTP API · WebSocket · Rust                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Capabilities (12)

### Voice & Intent Processing
- **E-SIRI-01**: Siri App Intents - Capture, query, and action intents
- **E-SIRI-02**: Announce Notifications - Spoken alerts via AirPods/CarPlay
- **E-SIRI-07**: Shortcuts & Automation - Automations and phrase triggers

### Visual Integration
- **E-SIRI-03**: Home & Lock Screen Widgets - Timeline-based data display
- **E-SIRI-04**: Live Activities & Dynamic Island - Real-time focus sessions
- **E-SIRI-06**: Spotlight Search Integration - System-wide content search

### System Integration
- **E-SIRI-05**: Background Sync - Bidirectional sync every 15 minutes
- **E-SIRI-08**: Apple Watch Complications - Glanceable data on watchOS
- **E-SIRI-09**: Handoff & Continuity - Seamless device transitions
- **E-SIRI-10**: Focus Mode Integration - Context-aware filtering
- **E-SIRI-11**: CarPlay Support - Driving-safe voice interaction
- **E-SIRI-12**: Local-First Architecture - Core Data with offline support

---

## Key Components

### 1. App Intents (6 Intents)

**CaptureThoughtIntent**
```swift
"Capture a thought in Kiro"
→ Prompts for content
→ Optional tags selection
→ Stores locally in Core Data
→ Background sync to backend
→ Response: "✅ Thought captured"
```

**QueryAgendaIntent**
```swift
"Get my Kiro agenda"
→ Timeframe: today/tomorrow/week
→ Fetches meetings + tasks
→ Spoken summary: "You have 3 meetings today..."
→ Returns: AgendaSnapshot with details
```

**LogHabitIntent**
```swift
"Log habit in Kiro"
→ Habit picker (dynamic options)
→ Marks complete in Core Data
→ Updates streak counter
→ Response: "✅ Logged Meditation. Streak: 7 days 🔥"
```

**CreateTaskIntent**
```swift
"Create task in Kiro"
→ Prompts for task title
→ Optional: project, priority, due date
→ Creates in Core Data
→ Response: "✅ Created task: {title}"
```

**SearchKiroIntent**
```swift
"Search Kiro for design docs"
→ Query input
→ Scope: all/thoughts/tasks/files
→ Returns: Top 10 results
```

### 2. Announce Notifications (4 Types)

**Morning Brief** (7:00 AM weekdays)
```
"Good morning! You have 3 meetings today.
Top priority: Finish PR #123.
2 overdue tasks."
```

**Task Reminder** (-15 min before due)
```
"Task Starting Soon: Standup meeting in 15 minutes"
Actions: [Mark Complete] [Snooze 10 min]
```

**Habit Reminder** (user-defined time)
```
"Habit Check-In: Time to log your Meditation"
Action: [Log Now]
```

**Budget Alert** (80% threshold)
```
"Budget Alert: You've spent $800 of $1000 on Dining this month"
```

### 3. Widgets (3 Widget Kinds)

**HabitStreakCircular** (accessoryCircular)
- Gauge visualization: 5/7 habits complete
- Center: "5" with fire emoji
- Inline: "🔥 7 day streak"

**NextTaskInline** (accessoryInline)
- "⏰ Standup meeting at 10:00 AM"

**DailySummaryMedium** (systemMedium)
- Header: "Today's Focus"
- Top 3 tasks with priority badges
- Stats row: Habits 5/7 | Meetings 3 | Overdue 2

### 4. Live Activities

**FocusSessionActivity** (Dynamic Island)
- Compact: 🧠 timer icon + elapsed minutes
- Expanded: Task name, progress bar, pause/resume button
- Lock Screen: Horizontal layout with session details
- Update frequency: Every 60 seconds
- Max duration: 4 hours

### 5. Workflows (2 Main Workflows)

**wf_morning_brief_siri** (Daily at 7:00 AM)
```yaml
Steps:
1. Parallel data collection (5 steps):
   - fetch_agenda (meetings, habits)
   - fetch_top_tasks (priority tasks)
   - check_overdue (count)
   - check_habits (streaks)
   - check_budget (alerts)
2. format_announcement (template rendering)
3. send_notification (Announce Notification)
4. log_execution

Target Duration: < 5 seconds
Success Rate: > 99%
```

**wf_background_sync** (Every 15 minutes)
```yaml
Phases:
1. Validation (pre-checks, acquire lock)
2. Upload (fetch pending, push, resolve conflicts, mark synced)
3. Download (pull changes, apply creates/updates/deletes)
4. Finalization (update timestamp, refresh widgets, release lock)

Target Duration: 15 seconds
Max Duration: 30 seconds (BGTaskScheduler limit)
Success Rate: > 98%
Conflict Strategy: last_write_wins (configurable)
```

### 6. Agents (1 Core Agent)

**agent_ios_sync_coordinator**
- Tier B model (claude-3-5-haiku / gemini-flash)
- 6 tools: fetch_pending_changes, push_to_backend, pull_from_backend, resolve_conflict, mark_synced, get_sync_status
- Execution pattern: reactive (triggered by workflows)
- Actor-isolated for thread safety
- Offline queue management with FIFO processing

---

## Privacy & Security (10 Rules)

### Rule 1: On-Device Intent Processing
- All intents resolve locally in < 500ms
- No audio transmitted to Personal OS backend
- Core Data provides immediate responses

### Rule 2: Siri Audio Privacy
- Siri audio never leaves Apple's servers
- Only transcribed text reaches app
- No voice biometric data stored

### Rule 3: Keychain Storage
- API tokens in Keychain with `.whenUnlockedThisDeviceOnly`
- Never stored in UserDefaults or plain files
- Automatic token rotation every 90 days

### Rule 4: Widget Data Minimization
- Redact sensitive content (amounts, names)
- Show aggregates only: "3 tasks" not task titles
- No financial details in widgets

### Rule 5: Announce Notification Opt-In
- Explicit consent required
- Default: OFF
- Rate limit: 10 announced notifications/hour

### Rule 6: Background Sync Transparency
- Settings UI shows: last sync time, data transferred, conflicts
- User can disable sync entirely
- WiFi-only mode available

### Rule 7: Local-First Data Ownership
- All data accessible offline
- Export to JSON/CSV anytime
- Backend sync is optional enhancement

### Rule 8: Intent Response Dialog Privacy
- No PII in Siri responses
- Generic success messages
- Sensitive data only in app UI

### Rule 9: Spotlight Indexing Control
- User can disable per content type
- Respects system privacy settings
- Deletion propagates to Spotlight immediately

### Rule 10: Rate Limiting
- Max 10 announced notifications/hour
- Max 6 background syncs/hour
- Prevents battery drain and notification fatigue

---

## Wire Contracts

**File**: `.nb/context/contracts/native_siri_wire_contracts.yaml` (589 lines)

Defines:
- 6 App Intent schemas with parameters, responses, Siri phrases
- 3 Dynamic Options Providers (tags, habits, projects)
- 4 Notification contracts with templates and schedules
- 3 Widget timeline contracts with data schemas
- 1 Live Activity configuration with Dynamic Island layouts
- Spotlight indexing attribute sets
- Error handling strategies
- Performance SLAs

---

## Performance Targets

| Metric | Target | Max | Notes |
|--------|--------|-----|-------|
| Intent Response Time (p50) | 200ms | 500ms | On-device only |
| Intent Response Time (p95) | 500ms | 1s | Network calls |
| Morning Brief Duration | 5s | 10s | Parallel data fetch |
| Background Sync Duration | 15s | 30s | BGTaskScheduler limit |
| Widget Timeline Generation | 2s | 5s | Per widget kind |
| Notification Delivery | 500ms | 1s | System priority |
| Live Activity Update | 100ms | 500ms | Every 60s |
| Memory Usage | - | 50MB | Background sync |
| Network Transfer | - | 10MB | Per sync session |

---

## Integration Points

### Personal OS Pillars (All 8)
- **Thoughts**: Capture via Siri, search in Spotlight
- **Projects**: Create tasks, query agenda
- **Activities**: Log habits, track streaks
- **Files**: Search and open via Siri
- **Finance**: Budget alerts via notifications
- **Interactions**: Meeting reminders
- **Memory**: Contextual recall in intents
- **Workflows**: Trigger automations via Shortcuts

### Apple Frameworks
- **AppIntents**: Core intent handling (iOS 16+)
- **UserNotifications**: Announce Notifications
- **WidgetKit**: Widget timeline providers
- **ActivityKit**: Live Activities & Dynamic Island
- **Core Data**: Local persistence
- **SwiftData**: Modern data layer (iOS 17+)
- **Keychain Services**: Secure credential storage
- **Core Spotlight**: System-wide search indexing
- **BGTaskScheduler**: Background sync scheduling
- **WatchConnectivity**: Apple Watch sync
- **CarPlay**: Driving-safe UI

---

## Development Phases

### Phase 1: Core Intents (4 weeks)
- Implement 6 App Intents
- Basic Core Data models
- API client with Keychain auth
- Siri phrase registration

### Phase 2: Notifications & Widgets (3 weeks)
- Morning brief workflow
- Announce Notification implementation
- 3 widget kinds with timeline providers
- Background sync with BGTaskScheduler

### Phase 3: Live Activities (2 weeks)
- Focus session Live Activity
- Dynamic Island layouts
- Lock Screen configuration
- Push notification updates

### Phase 4: Advanced Integration (3 weeks)
- Spotlight indexing
- Apple Watch complications
- Handoff & Continuity
- CarPlay support
- Focus Mode integration

### Phase 5: Polish & Testing (2 weeks)
- Performance optimization
- Privacy rule enforcement
- User acceptance testing
- App Store submission

**Total Estimated Duration**: 14 weeks

---

## Files Created

### Extension Specification
1. `.nb/plan/extensions/native_apple_siri/README.md` (1,245 lines)
2. `.nb/plan/extensions/native_apple_siri/MANIFEST.yaml` (147 lines)
3. `.nb/plan/extensions/native_apple_siri/concise.md` (518 lines)

### Wire Contracts & Rules
4. `.nb/context/contracts/native_siri_wire_contracts.yaml` (589 lines)
5. `.nb/context/rules/native_siri_privacy_rules.md` (468 lines)

### Agents & Workflows
6. `.nb/agentic/custom/agents/agent_ios_sync_coordinator.yaml` (468 lines)
7. `.nb/agentic/custom/workflows/wf_morning_brief_siri.yaml` (364 lines)
8. `.nb/agentic/custom/workflows/wf_background_sync.yaml` (481 lines)

### Extension Index
9. `.nb/plan/extensions/README.md` (Updated, now lists 3 complete extensions)

**Total Lines**: ~4,280 lines of specification

---

## Success Metrics

### User Engagement
- Siri intent invocations/day > 10
- Widget views/day > 50
- Morning brief open rate > 70%
- Background sync success rate > 98%

### Performance
- Intent response time p95 < 500ms
- Background sync duration p95 < 20s
- Battery impact < 3% per day
- Network usage < 100MB per day

### Privacy Compliance
- Zero privacy rule violations
- Zero unauthorized data transmissions
- 100% user consent for Announce Notifications
- All credentials in Keychain

### Quality
- App Store rating > 4.5 stars
- Crash-free sessions > 99.9%
- Background task completion rate > 95%
- Widget refresh success rate > 99%

---

## Next Steps

1. **Implementation**: Begin Phase 1 (Core Intents) development
2. **Design Assets**: Create app icons, widget previews, marketing materials
3. **TestFlight**: Set up beta testing program
4. **Documentation**: Write user guide and developer documentation
5. **App Store**: Prepare listing with screenshots and privacy details

---

## Related Extensions

- **Voice Interface** (Whisper-based): Custom wake word detection, offline transcription
- **Email Triage**: Intelligent inbox processing with entity extraction
- **Proactive Intelligence**: Pattern learning and anomaly detection (planned)

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Begin Swift/SwiftUI development (Phase 1)
