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

# Layerable Extension Plan: Native Apple Apps with Siri Integration

### Executive Overview
Native iOS/macOS companion apps that integrate Personal OS with Apple's ecosystem through **SiriKit App Intents, Announce Notifications, Shortcuts, Widgets, and Live Activities**. Enables voice control, proactive suggestions, and system-level integration without custom wake word detection—leveraging Apple's native Siri infrastructure.

---

## 1. Extension-Specific Quad-Space Mapping

```
.
├── context/
│   ├── contracts/
│   │   ├── native_siri_wire_contracts.yaml     # App Intent schemas, notification payloads
│   │   ├── native_siri_widget_contracts.yaml   # Widget timeline provider specs
│   │   └── native_siri_sync_protocol.yaml      # iOS ↔ Personal OS sync protocol
│   └── rules/
│       ├── native_siri_privacy_rules.md         # Apple privacy guidelines compliance
│       └── native_siri_background_rules.md      # Background processing limits
├── agentic/
│   ├── custom/agents/
│   │   ├── agent_ios_sync_coordinator.yaml      # iOS ↔ backend sync orchestrator (Tier B)
│   │   └── agent_widget_data_provider.yaml      # Widget timeline generation (Tier B)
│   └── custom/workflows/
│       ├── wf_morning_brief_siri.yaml           # Morning brief via Announce Notifications
│       ├── wf_background_sync.yaml              # Background URLSession sync
│       └── wf_focus_session_activity.yaml       # Live Activity management
├── workplace/
│   ├── modules/
│   │   ├── kiro_ios/                            # iOS app (Swift/SwiftUI)
│   │   ├── kiro_macos/                          # macOS app
│   │   ├── kiro_watchos/                        # watchOS companion
│   │   └── kiro_shared/                         # Shared Swift Package
│   └── integrations/
│       ├── pos_api_client/                      # Swift client for Personal OS REST API
│       └── pos_sync_engine/                     # Core Data + background sync
└── user/
    ├── inputs/
    │   ├── siri_shortcuts_config.yaml           # User-defined shortcuts
    │   └── widget_preferences.yaml              # Widget layout preferences
    └── outputs/
        └── spotlight_index/                     # Indexed content for Spotlight
```

---

## 2. Siri Integration Wire Contracts

### 2.1. App Intents Contract (`context/contracts/native_siri_wire_contracts.yaml`)

```yaml
schema_version: "1.0.0"
domain: "native_siri_integration"
framework: "AppIntents (iOS 16+)"

# Core App Intents
intents:
  - id: "CaptureThoughtIntent"
    display_name: "Capture Thought"
    description: "Quickly capture a thought or idea"
    parameters:
      - name: "content"
        type: "String"
        required: true
        prompt: "What's on your mind?"
      - name: "tags"
        type: "[String]"
        required: false
        options_provider: "TagsOptionsProvider"
    siri_phrases:
      - "Capture a thought in Kiro"
      - "Add note to Kiro"
      - "Quick capture in Kiro"
    response_dialog: "✅ Thought captured"
    
  - id: "QueryAgendaIntent"
    display_name: "Get My Agenda"
    description: "View upcoming tasks and meetings"
    parameters:
      - name: "timeframe"
        type: "AgendaTimeframe"
        required: true
        default: "today"
        enum: ["today", "tomorrow", "thisWeek", "nextWeek"]
    siri_phrases:
      - "Get my Kiro agenda"
      - "What's on my Kiro schedule"
      - "Show my Kiro day"
    returns:
      type: "AgendaSnapshot"
      fields:
        - "meetingCount: Int"
        - "topTask: Task?"
        - "overdueCount: Int"
        - "meetings: [Meeting]"
        - "tasks: [Task]"
    
  - id: "LogHabitIntent"
    display_name: "Log Habit"
    description: "Mark a habit as complete"
    parameters:
      - name: "habitID"
        type: "String"
        required: true
        options_provider: "HabitsOptionsProvider"
    siri_phrases:
      - "Log habit in Kiro"
      - "Mark habit complete in Kiro"
    response_dialog: "✅ Logged {habitName}. Streak: {streak} days 🔥"
    
  - id: "CreateTaskIntent"
    display_name: "Create Task"
    description: "Create a new task"
    parameters:
      - name: "title"
        type: "String"
        required: true
        prompt: "What's the task?"
      - name: "projectID"
        type: "String"
        required: false
        options_provider: "ProjectsOptionsProvider"
      - name: "priority"
        type: "TaskPriority"
        required: false
        default: "medium"
        enum: ["low", "medium", "high"]
      - name: "dueDate"
        type: "Date"
        required: false
    siri_phrases:
      - "Create task in Kiro"
      - "Add task to Kiro"
    response_dialog: "✅ Created task: {title}"

# Dynamic Options Providers
options_providers:
  - id: "TagsOptionsProvider"
    endpoint: "/api/v1/thoughts/tags"
    cache_ttl: 3600  # 1 hour
    
  - id: "HabitsOptionsProvider"
    endpoint: "/api/v1/activities/habits"
    cache_ttl: 86400  # 24 hours
    
  - id: "ProjectsOptionsProvider"
    endpoint: "/api/v1/projects"
    cache_ttl: 3600
```

### 2.2. Announce Notifications Contract

```yaml
# Notification Types
notification_types:
  - id: "morning_brief"
    title: "Your Kiro Daily Brief"
    body_template: |
      Good morning! You have {meetingCount} meetings today.
      Top priority: {topTask}.
      {overdueAlert}
    interruption_level: "timeSensitive"
    sound: "default"
    announce: true
    schedule: "7:00 AM weekdays"
    
  - id: "task_reminder"
    title: "Task Starting Soon"
    body_template: "{taskTitle} is scheduled in 15 minutes"
    interruption_level: "active"
    sound: "default"
    announce: true
    schedule: "dynamic (15 min before task)"
    
  - id: "habit_reminder"
    title: "Habit Check-In"
    body_template: "Time to log your {habitName}"
    interruption_level: "passive"
    sound: "subtle"
    announce: false
    schedule: "user-defined"
    
  - id: "budget_alert"
    title: "Budget Alert"
    body_template: "You've spent ${spent} of ${limit} on {category} this month"
    interruption_level: "timeSensitive"
    sound: "critical"
    announce: true
    schedule: "dynamic (80% threshold reached)"

# Announcement Configuration
announcement_settings:
  enabled_contexts:
    - "airpods"
    - "carplay"
    - "homepod"
    - "speaker"
  respect_focus_modes: true
  suppress_when_screen_on: false
  rate_limit: "max 10 per hour"
```

---

## 3. Widget Specifications

### 3.1. Lock Screen Widgets

```yaml
lock_screen_widgets:
  - id: "HabitStreakCircular"
    family: "accessoryCircular"
    update_frequency: "hourly"
    data_source: "/api/v1/activities/habits/summary"
    display:
      type: "gauge"
      value: "completedToday"
      total: "totalHabits"
      center_text: "{completedToday}"
      
  - id: "NextTaskInline"
    family: "accessoryInline"
    update_frequency: "15_minutes"
    data_source: "/api/v1/projects/tasks/next"
    display:
      type: "text"
      format: "⏰ {title} at {dueTime}"
      
  - id: "HabitProgressRectangular"
    family: "accessoryRectangular"
    update_frequency: "hourly"
    data_source: "/api/v1/activities/habits/summary"
    display:
      header: "Habits Today"
      main_text: "{completedToday}/{totalHabits}"
      trailing: "🔥 {longestStreak}"
```

### 3.2. Home Screen Widgets

```yaml
home_screen_widgets:
  - id: "DailySummaryMedium"
    family: "systemMedium"
    update_frequency: "15_minutes"
    data_source: "/api/v1/activities/agenda?timeframe=today"
    sections:
      - type: "header"
        text: "Today's Focus"
      - type: "task_list"
        max_items: 3
        show_priority_badge: true
      - type: "stats_row"
        metrics: ["habits", "meetings", "overdue"]
        
  - id: "WeeklyGoalsLarge"
    family: "systemLarge"
    update_frequency: "hourly"
    data_source: "/api/v1/activities/habits/weekly"
    sections:
      - type: "header"
        text: "This Week"
      - type: "habit_grid"
        layout: "7x5"  # 7 days × 5 habits
      - type: "streak_summary"
```

---

## 4. Live Activities Implementation

### 4.1. Focus Session Activity

```yaml
live_activity:
  id: "FocusSession"
  attributes:
    sessionID: "UUID"
    taskName: "String"
  content_state:
    elapsedMinutes: "Int"
    totalMinutes: "Int"
    isBreak: "Bool"
    
  dynamic_island:
    compact_leading: "🧠 icon (focus) or ☕️ icon (break)"
    compact_trailing: "{elapsedMinutes} min"
    minimal: "timer icon"
    expanded:
      leading_region: "{taskName}"
      trailing_region: "{elapsedMinutes} min"
      bottom_region: "ProgressView"
      
  lock_screen:
    layout: "horizontal"
    left: "Task name + status"
    right: "{elapsedMinutes}/{totalMinutes} min"
    
  update_cadence: "every 60 seconds"
  max_duration: "4 hours"
  end_stale_date: "session end time + 5 minutes"
```

---

## 5. Shortcuts Configuration

### 5.1. Predefined Shortcuts

```yaml
shortcuts:
  - id: "morning_routine"
    name: "Kiro Morning Routine"
    icon: "sun.horizon"
    actions:
      - intent: "QueryAgendaIntent"
        parameters:
          timeframe: "today"
      - action: "show_result"
        format: "spoken + visual"
      - action: "update_widget"
        widget: "DailySummaryMedium"
    triggers:
      - type: "time"
        schedule: "7:00 AM weekdays"
      - type: "automation"
        condition: "alarm dismissed"
        
  - id: "quick_capture"
    name: "Quick Kiro Capture"
    icon: "lightbulb"
    actions:
      - action: "ask_for_input"
        prompt: "What's on your mind?"
      - intent: "CaptureThoughtIntent"
        parameters:
          content: "{input}"
      - action: "show_notification"
        message: "✅ Captured"
    triggers:
      - type: "back_tap"
        taps: 2
      - type: "nfc"
        tag: "desk_tag"
        
  - id: "evening_reflection"
    name: "Evening Reflection"
    icon: "moon.stars"
    actions:
      - action: "ask_for_input"
        prompt: "How was your day?"
        multiline: true
      - intent: "CaptureThoughtIntent"
        parameters:
          content: "{input}"
          tags: ["journal", "daily_reflection"]
      - action: "show_widget"
        widget: "HabitProgressRectangular"
    triggers:
      - type: "time"
        schedule: "9:00 PM daily"
        
  - id: "commute_context"
    name: "Commute Brief"
    icon: "car.fill"
    actions:
      - intent: "QueryAgendaIntent"
        parameters:
          timeframe: "today"
      - action: "announce_via_siri"
      - action: "set_navigation"
        condition: "has upcoming meeting with location"
    triggers:
      - type: "carplay_connect"
      - type: "location"
        region: "leaving home radius"
```

---

## 6. Background Sync Protocol

### 6.1. Sync Strategy

```yaml
background_sync:
  framework: "BGTaskScheduler"
  task_identifier: "com.kiro.background-sync"
  
  sync_triggers:
    - type: "periodic"
      interval: 900  # 15 minutes
      earliest_begin_date: "now + 15 minutes"
      requires_network: true
      requires_charging: false
      
    - type: "app_refresh"
      frequency: "hourly"
      
    - type: "push_notification"
      priority: "high"
      
  sync_operations:
    - operation: "fetch_agenda"
      endpoint: "/api/v1/activities/agenda"
      priority: "high"
      
    - operation: "sync_thoughts"
      endpoint: "/api/v1/thoughts/sync"
      priority: "medium"
      
    - operation: "sync_tasks"
      endpoint: "/api/v1/projects/tasks/sync"
      priority: "medium"
      
    - operation: "update_habit_streaks"
      endpoint: "/api/v1/activities/habits/streaks"
      priority: "low"
      
  data_limits:
    max_transfer_size: "10 MB"
    timeout: 30  # seconds
    retry_policy: "exponential_backoff"
```

---

## 7. Core Data Schema

### 7.1. Local Persistence Models

```swift
// Thought Entity
@Model
class ThoughtEntity {
    @Attribute(.unique) var id: UUID
    var content: String
    var createdAt: Date
    var tags: [String]
    var syncStatus: SyncStatus
    var lastSyncedAt: Date?
}

// Task Entity
@Model
class TaskEntity {
    @Attribute(.unique) var id: UUID
    var title: String
    var projectID: String?
    var priority: String
    var status: String
    var dueDate: Date?
    var syncStatus: SyncStatus
}

// Habit Entity
@Model
class HabitEntity {
    @Attribute(.unique) var id: UUID
    var name: String
    var streak: Int
    var lastLoggedAt: Date?
    var completedToday: Bool
}

// Sync Status
enum SyncStatus: String, Codable {
    case synced
    case pending
    case failed
    case conflict
}
```

---

## 8. Privacy & Security Rules

### 8.1. Privacy Compliance (`context/rules/native_siri_privacy_rules.md`)

**Rule 1: On-Device Intent Processing**
- All App Intents use `.applicationData` property for on-device processing when possible
- No sensitive data in intent response dialogs (visible in Shortcuts)
- Siri audio never sent to Personal OS servers

**Rule 2: Keychain Storage**
- API tokens stored in Keychain with `.whenUnlockedThisDeviceOnly` accessibility
- Background sync uses ephemeral session tokens (1-hour TTL)
- No plaintext credentials in UserDefaults or Core Data

**Rule 3: Background Sync Transparency**
- User-visible sync indicator in app
- Last sync timestamp displayed
- Network usage tracked and displayed in settings

**Rule 4: Widget Data Minimization**
- Widgets show summary data only (no sensitive details)
- Redact task titles containing keywords: password, secret, private
- User can disable widgets per-type

**Rule 5: Announce Notification Opt-In**
- Explicit permission request for announcement capability
- User can disable per-notification-type
- Respect Do Not Disturb and Focus modes

---

## 9. Agent Specifications

### 9.1. iOS Sync Coordinator Agent

```yaml
# .nb/agentic/custom/agents/agent_ios_sync_coordinator.yaml
agent_id: "agent_ios_sync_coordinator"
name: "iOS Sync Coordinator"
model_tier: "tier_b"
responsibility: "Orchestrate bidirectional sync between iOS app and Personal OS backend"

tools:
  - id: "fetch_pending_changes"
    description: "Get local changes not yet synced"
    schema:
      input: { device_id: string }
      output: { thoughts: Thought[], tasks: Task[], habits: Habit[] }
      
  - id: "push_to_backend"
    description: "Upload local changes to Personal OS"
    schema:
      input: { changes: Changes, batch_size: int }
      output: { synced_ids: string[], conflicts: Conflict[] }
      
  - id: "pull_from_backend"
    description: "Download remote changes"
    schema:
      input: { last_sync_timestamp: ISO8601, device_id: string }
      output: { remote_changes: Changes }
      
  - id: "resolve_conflict"
    description: "Handle sync conflicts (last-write-wins or manual)"
    schema:
      input: { conflict: Conflict, resolution_strategy: enum }
      output: { resolved_entity: Entity }

execution_pattern: "reactive"
triggers:
  - "background_task_scheduled"
  - "app_did_become_active"
  - "significant_local_change"
```

---

## 10. Workflow Specifications

### 10.1. Morning Brief Workflow

```yaml
# .nb/agentic/custom/workflows/wf_morning_brief_siri.yaml
workflow_id: "wf_morning_brief_siri"
name: "Morning Brief via Siri Announcement"
trigger: "scheduled (7:00 AM weekdays)"

steps:
  - id: "fetch_agenda"
    agent: "agent_activity_scheduler"
    tool: "get_daily_agenda"
    input:
      date: "today"
      
  - id: "fetch_top_tasks"
    agent: "agent_project_orchestrator"
    tool: "get_priority_tasks"
    input:
      limit: 3
      
  - id: "check_overdue"
    agent: "agent_project_orchestrator"
    tool: "count_overdue_tasks"
    
  - id: "format_announcement"
    agent: "agent_ios_sync_coordinator"
    tool: "format_notification_text"
    input:
      template: "morning_brief"
      data:
        meeting_count: "${fetch_agenda.meeting_count}"
        top_task: "${fetch_top_tasks[0].title}"
        overdue_count: "${check_overdue.count}"
        
  - id: "schedule_notification"
    action: "send_to_ios_app"
    input:
      notification_type: "morning_brief"
      content: "${format_announcement.text}"
      announce: true

error_handling:
  on_api_failure: "send_fallback_notification"
  on_timeout: "log_and_retry_tomorrow"
```

---

## 11. CLI Integration

### 11.1. Personal OS CLI Commands for iOS

```bash
# Generate iOS API client code
pos ios generate-client --output kiro_ios/Sources/KiroAPIClient

# Test iOS sync locally
pos ios test-sync --device-id "iPhone-Lakhwinder"

# Push test notification to iOS
pos ios notify --title "Test" --body "Hello from Personal OS" --announce

# View iOS sync status
pos ios sync-status
# Output:
# Last sync: 2 minutes ago
# Pending uploads: 3 thoughts, 1 task
# Conflicts: 0

# Reset iOS device registration
pos ios reset-device --device-id "iPhone-Lakhwinder"
```

---

## 12. Performance Targets

| Metric | Target | Measurement |
|---|---|---|
| Intent response time | < 500ms | Time from Siri request to result |
| Widget timeline generation | < 2s | TimelineProvider getTimeline() |
| Background sync completion | < 30s | BGTaskScheduler task duration |
| Notification delivery | < 1s | Local notification scheduling |
| Live Activity update | < 100ms | Activity.update() latency |
| Core Data query (typical) | < 50ms | NSFetchRequest execution time |
| Spotlight reindex | < 5s | Full reindex of all searchable items |

---

## 13. Implementation Phases

### Phase 1: Core iOS App (Weeks 1-3)
```swift
// File structure
kiro_ios/
├── Sources/
│   ├── Views/
│   │   ├── DashboardView.swift
│   │   ├── ThoughtsListView.swift
│   │   └── TasksListView.swift
│   ├── Models/
│   │   ├── ThoughtEntity.swift
│   │   └── TaskEntity.swift
│   ├── Services/
│   │   ├── KiroAPIClient.swift
│   │   └── SyncManager.swift
│   └── KiroApp.swift
└── Info.plist
```

### Phase 2: App Intents (Week 4-5)
- Define all AppIntent types
- Implement intent handlers
- Add Siri phrase suggestions
- Test with Shortcuts app

### Phase 3: Widgets (Week 6-7)
- Lock screen widgets (circular, inline, rectangular)
- Home screen widgets (medium, large)
- Timeline providers with smart refresh
- Deep link handling

### Phase 4: Notifications & Live Activities (Week 8-9)
- Announce Notifications setup
- Morning brief automation
- Focus Session Live Activity
- Dynamic Island integration

### Phase 5: Background Sync (Week 10)
- BGTaskScheduler integration
- Conflict resolution strategy
- Offline queue management
- Network reachability handling

### Phase 6: Apple Watch (Week 11-12)
- watchOS companion app
- Complications (circular, rectangular)
- Quick actions
- WatchConnectivity sync

---

## 14. Success Metrics

**Engagement**
- Daily active Siri commands: > 5 per user
- Widget views per day: > 20
- Shortcut automation triggers: > 3 per day

**Performance**
- 95th percentile intent response: < 500ms
- Background sync success rate: > 99%
- Conflict resolution accuracy: > 95% (last-write-wins)

**Privacy**
- Zero cloud-transmitted Siri audio
- Zero plaintext credential exposure
- User-controlled announcement permissions

---

**Status**: ✅ Specification Complete  
**Integration Ready**: All wire contracts defined, agent tools specified  
**Next Action**: Begin Phase 1 iOS app development with SwiftUI + Core Data
