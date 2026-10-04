# Native Apple Siri Integration: Privacy & Security Rules

**Domain**: Native iOS/macOS Siri Integration  
**Version**: 1.0.0  
**Last Updated**: 2024-10-04  
**Compliance**: Apple Privacy Guidelines, GDPR, CCPA

---

## Overview

These rules govern how Personal OS integrates with Apple's Siri, Shortcuts, and notification systems while maintaining user privacy and data security. All rules are **mandatory** and must be enforced in the iOS/macOS app implementation.

---

## Rule 1: On-Device Intent Processing

**Requirement**: All App Intents must process data on-device whenever possible, without transmitting sensitive information to Personal OS servers until necessary.

### Implementation

```swift
// ✅ CORRECT: Process intent on-device, only sync result
struct CaptureThoughtIntent: AppIntent {
    func perform() async throws -> some IntentResult {
        // 1. Create local entity immediately
        let thought = ThoughtEntity(content: content, tags: tags)
        try await LocalStorage.save(thought)
        
        // 2. Mark for background sync (non-blocking)
        await SyncQueue.enqueue(thought, priority: .low)
        
        // 3. Return immediately
        return .result(dialog: "✅ Thought captured")
    }
}

// ❌ WRONG: Block on network request
struct CaptureThoughtIntent: AppIntent {
    func perform() async throws -> some IntentResult {
        // This blocks Siri until network completes
        let response = try await KiroAPI.createThought(content: content)
        return .result(dialog: "✅ Thought captured")
    }
}
```

### Audit Points

- [ ] Intent `perform()` methods return within 500ms
- [ ] Network calls are non-blocking (queued for background sync)
- [ ] Local Core Data entities created before sync
- [ ] User sees success confirmation immediately

**Why**: Siri intents must respond quickly. Network latency or failures shouldn't block user interaction.

---

## Rule 2: Siri Audio Privacy

**Requirement**: Siri audio recordings are **never** transmitted to Personal OS servers. Only the transcribed text (processed by Apple) reaches the app.

### What We Receive

```swift
// ✅ What the app receives from Siri
struct CaptureThoughtIntent: AppIntent {
    @Parameter(title: "Content")
    var content: String  // ← Already transcribed by Apple
    
    // We NEVER receive:
    // - Raw audio data
    // - Siri voice recordings
    // - Speech confidence scores
}
```

### Logging Policy

```swift
// ✅ ALLOWED: Log intent parameters
logger.info("CaptureThoughtIntent executed", metadata: [
    "content_length": content.count,
    "tag_count": tags?.count ?? 0
])

// ❌ FORBIDDEN: Log raw audio or Siri metadata
logger.info("Siri audio received")  // This never happens
```

### User Communication

App privacy policy must state:
> "Personal OS integrates with Siri using Apple's AppIntents framework. Only the text transcribed by Siri (on your device) is processed by Personal OS. We never receive, store, or transmit Siri audio recordings."

**Why**: Users trust Apple with voice data, not third-party apps. Maintaining this boundary is critical for user trust.

---

## Rule 3: Keychain Storage for Credentials

**Requirement**: All authentication tokens and API credentials must be stored in iOS Keychain with `.whenUnlockedThisDeviceOnly` accessibility.

### Implementation

```swift
// ✅ CORRECT: Secure keychain storage
class SecureStorage {
    func saveAPIToken(_ token: String) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: "kiro_api_token",
            kSecValueData as String: token.data(using: .utf8)!,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        SecItemAdd(query as CFDictionary, nil)
    }
}

// ❌ FORBIDDEN: UserDefaults, Core Data, or files
UserDefaults.standard.set(apiToken, forKey: "token")  // ❌ Plaintext!
try CoreData.save(APIToken(value: token))  // ❌ Unencrypted!
try token.write(to: fileURL)  // ❌ File system exposure!
```

### Accessibility Levels

| Level | When Available | Use Case |
|---|---|---|
| `whenUnlockedThisDeviceOnly` | Device unlocked, no iCloud sync | ✅ **API tokens** (our default) |
| `afterFirstUnlockThisDeviceOnly` | After first unlock, even if locked | Background sync tokens (1-hour TTL) |
| `whenUnlocked` | Device unlocked, syncs via iCloud Keychain | ❌ Never use (syncs to other devices) |

### Token Rotation

```swift
// Background sync uses short-lived tokens
struct BackgroundSyncToken {
    let value: String
    let expiresAt: Date  // Max 1 hour TTL
}

// Main API token is long-lived
struct MainAPIToken {
    let value: String
    let refreshToken: String
    let expiresAt: Date  // 30 days
}
```

**Why**: Keychain is hardware-encrypted and isolated from app sandbox. UserDefaults and Core Data are not encrypted by default.

---

## Rule 4: Widget Data Minimization

**Requirement**: Widgets must show **summary data only**. No sensitive task titles, full thought content, or personally identifiable information.

### Content Redaction

```swift
// ✅ CORRECT: Redact sensitive content
struct DailySummaryWidget: Widget {
    func timeline(for configuration: Configuration, in context: Context) async -> Timeline<Entry> {
        let tasks = await fetchTasks()
        
        let redactedTasks = tasks.map { task in
            var safe = task
            // Redact sensitive keywords
            if task.title.lowercased().contains(["password", "secret", "private", "ssn", "api key"]) {
                safe.title = "🔒 Private Task"
            }
            // Truncate long titles
            if safe.title.count > 40 {
                safe.title = String(safe.title.prefix(37)) + "..."
            }
            return safe
        }
        
        return Timeline(entries: [Entry(tasks: redactedTasks)], policy: .after(Date().addingTimeInterval(900)))
    }
}

// ❌ FORBIDDEN: Show raw sensitive data
Text(task.title)  // Could be "Reset AWS root password - ABC123"
```

### User Controls

```swift
// Settings UI
struct WidgetSettingsView: View {
    @AppStorage("widgets.showTaskDetails") var showTaskDetails = false
    @AppStorage("widgets.showThoughts") var showThoughts = false
    
    var body: some View {
        Form {
            Section("Privacy") {
                Toggle("Show task details in widgets", isOn: $showTaskDetails)
                Toggle("Show recent thoughts", isOn: $showThoughts)
            }
            
            Text("Widgets are visible on your lock screen. Disable details for sensitive content.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }
}
```

**Why**: Lock screen widgets are visible without authentication. Anyone who sees your lock screen sees widget content.

---

## Rule 5: Announce Notification Opt-In

**Requirement**: Users must **explicitly opt-in** to Siri Announce Notifications. Default is **OFF**.

### Permission Flow

```swift
// ✅ CORRECT: Explicit opt-in with explanation
class OnboardingView: View {
    @State private var showingAnnouncementPermission = false
    
    var body: some View {
        VStack {
            Image(systemName: "airpodspro")
                .font(.system(size: 60))
            
            Text("Siri Announcements")
                .font(.title.bold())
            
            Text("Get your morning brief and task reminders spoken through your AirPods or CarPlay.")
                .multilineTextAlignment(.center)
                .padding()
            
            Button("Enable Announcements") {
                Task {
                    try await requestAnnouncementPermission()
                }
            }
            
            Button("Skip") {
                // Continue without announcements
            }
            .foregroundStyle(.secondary)
        }
    }
    
    func requestAnnouncementPermission() async throws {
        let options: UNAuthorizationOptions = [
            .alert,
            .sound,
            .badge,
            .announcement  // ← Explicit announcement capability
        ]
        
        try await UNUserNotificationCenter.current().requestAuthorization(options: options)
    }
}

// ❌ FORBIDDEN: Request all permissions silently
try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .announcement])
// No explanation shown to user!
```

### Per-Notification-Type Control

```swift
// Settings UI
struct NotificationSettingsView: View {
    @AppStorage("notify.morningBrief.enabled") var morningBriefEnabled = true
    @AppStorage("notify.morningBrief.announce") var morningBriefAnnounce = false
    
    @AppStorage("notify.taskReminder.enabled") var taskReminderEnabled = true
    @AppStorage("notify.taskReminder.announce") var taskReminderAnnounce = true
    
    var body: some View {
        Form {
            Section("Morning Brief") {
                Toggle("Enabled", isOn: $morningBriefEnabled)
                if morningBriefEnabled {
                    Toggle("Announce via Siri", isOn: $morningBriefAnnounce)
                }
            }
            
            Section("Task Reminders") {
                Toggle("Enabled", isOn: $taskReminderEnabled)
                if taskReminderEnabled {
                    Toggle("Announce via Siri", isOn: $taskReminderAnnounce)
                }
            }
        }
    }
}
```

### Respect Focus Modes

```swift
// ✅ Respect user's Focus settings
let content = UNMutableNotificationContent()
content.interruptionLevel = .timeSensitive  // Not .critical
content.sound = .default

// System automatically respects:
// - Do Not Disturb
// - Sleep Focus
// - Work Focus (if configured to allow Kiro)
```

**Why**: Spoken notifications through AirPods are more intrusive than visual notifications. Users must consciously opt-in.

---

## Rule 6: Background Sync Transparency

**Requirement**: Users must be able to see when background sync occurs and how much data is transferred.

### Sync Status UI

```swift
struct SyncStatusView: View {
    @ObservedObject var syncManager = SyncManager.shared
    
    var body: some View {
        GroupBox {
            HStack {
                Image(systemName: syncManager.isSyncing ? "arrow.triangle.2.circlepath" : "checkmark.circle.fill")
                    .foregroundStyle(syncManager.isSyncing ? .blue : .green)
                
                VStack(alignment: .leading) {
                    Text(syncManager.isSyncing ? "Syncing..." : "All synced")
                        .font(.subheadline.bold())
                    
                    if let lastSync = syncManager.lastSyncDate {
                        Text("Last sync: \(lastSync, style: .relative) ago")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                
                Spacer()
                
                // Data usage
                VStack(alignment: .trailing) {
                    Text(syncManager.totalDataTransferred.formatted(.byteCount(style: .file)))
                        .font(.caption.monospacedDigit())
                    Text("this month")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}
```

### Sync Logs (Debug Mode)

```swift
// Available in Settings > Advanced > Sync Logs
struct SyncLogView: View {
    @State private var logs: [SyncLog] = []
    
    var body: some View {
        List(logs) { log in
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(log.timestamp, style: .time)
                        .font(.caption.monospacedDigit())
                    Spacer()
                    Label("\(log.uploaded) up", systemImage: "arrow.up")
                        .font(.caption)
                    Label("\(log.downloaded) down", systemImage: "arrow.down")
                        .font(.caption)
                }
                Text(log.summary)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .navigationTitle("Sync History")
    }
}

struct SyncLog: Identifiable {
    let id = UUID()
    let timestamp: Date
    let uploaded: Int  // item count
    let downloaded: Int
    let summary: String
}
```

### Network Reachability

```swift
// Respect user's network preferences
class SyncManager {
    @AppStorage("sync.wifiOnly") var wifiOnly = false
    
    func shouldSync() -> Bool {
        guard NetworkMonitor.shared.isConnected else { return false }
        
        if wifiOnly && NetworkMonitor.shared.connectionType == .cellular {
            logger.info("Skipping sync: Wi-Fi only mode enabled")
            return false
        }
        
        return true
    }
}
```

**Why**: Background operations that consume data or battery should be transparent. Users have a right to know what their apps are doing.

---

## Rule 7: Local-First Data Ownership

**Requirement**: All data is stored locally first. Sync to Personal OS backend is **optional** and user-controlled.

### Data Flow

```
1. User creates thought via Siri
   ↓
2. Saved to local Core Data immediately (< 50ms)
   ↓
3. Success feedback shown to user
   ↓
4. [Later] Background sync uploads to Personal OS (if sync enabled)
   ↓
5. [Later] Conflict resolution if needed
```

### Offline Mode

```swift
// ✅ App works fully offline
class KiroApp: App {
    @State private var isOnline = false
    
    var body: some Scene {
        WindowGroup {
            ContentView()
                .task {
                    // Monitor network, but don't block UI
                    for await status in NetworkMonitor.shared.statusStream {
                        isOnline = status.isConnected
                    }
                }
                .toolbar {
                    if !isOnline {
                        Label("Offline", systemImage: "wifi.slash")
                            .foregroundStyle(.orange)
                    }
                }
        }
    }
}
```

### Data Export

```swift
// Users can export all local data
struct DataExportView: View {
    func exportAllData() async throws {
        let thoughts = try await LocalStorage.fetchAllThoughts()
        let tasks = try await LocalStorage.fetchAllTasks()
        
        let json = [
            "thoughts": thoughts.map { $0.toDictionary() },
            "tasks": tasks.map { $0.toDictionary() }
        ]
        
        let data = try JSONSerialization.data(withJSONObject: json, options: .prettyPrinted)
        
        // Present share sheet
        let url = FileManager.default.temporaryDirectory.appendingPathComponent("kiro_export.json")
        try data.write(to: url)
        
        shareSheet.present(url)
    }
}
```

**Why**: Users own their data. The app must work without a backend connection, and users must be able to export their data at any time.

---

## Rule 8: Intent Response Dialog Privacy

**Requirement**: Siri response dialogs must **not** contain sensitive information, as they appear in Shortcuts logs and Siri history.

### Safe Response Dialogs

```swift
// ✅ SAFE: Generic confirmation
return .result(dialog: "✅ Thought captured")

// ✅ SAFE: Non-sensitive summary
return .result(dialog: "✅ Logged morning exercise. 7 day streak!")

// ❌ UNSAFE: Contains sensitive task details
return .result(dialog: "✅ Created task: Reset production database password")

// ❌ UNSAFE: Contains PII
return .result(dialog: "✅ Added meeting with John Doe at 555-1234")
```

### Redaction Strategy

```swift
struct CreateTaskIntent: AppIntent {
    func perform() async throws -> some IntentResult {
        let task = try await createTask()
        
        // Redact sensitive content from Siri response
        let safeTitle = redactSensitive(task.title)
        
        return .result(dialog: "✅ Created task: \(safeTitle)")
    }
    
    func redactSensitive(_ text: String) -> String {
        let sensitivePatterns = [
            "password", "secret", "key", "token",
            "ssn", "credit card", "private"
        ]
        
        for pattern in sensitivePatterns {
            if text.lowercased().contains(pattern) {
                return "🔒 Private Task"
            }
        }
        
        // Truncate if too long
        return text.count > 50 ? String(text.prefix(47)) + "..." : text
    }
}
```

**Why**: Siri maintains a history of interactions, and Shortcuts logs all intent results. Sensitive data in responses could be exposed.

---

## Rule 9: Spotlight Indexing Control

**Requirement**: Users must be able to control what content is indexed in Spotlight and disable indexing entirely.

### User Controls

```swift
struct SearchSettingsView: View {
    @AppStorage("spotlight.enabled") var spotlightEnabled = true
    @AppStorage("spotlight.indexThoughts") var indexThoughts = true
    @AppStorage("spotlight.indexTasks") var indexTasks = true
    @AppStorage("spotlight.indexFiles") var indexFiles = false
    
    var body: some View {
        Form {
            Section {
                Toggle("Enable Spotlight Search", isOn: $spotlightEnabled)
            }
            
            if spotlightEnabled {
                Section("Indexed Content") {
                    Toggle("Thoughts", isOn: $indexThoughts)
                    Toggle("Tasks", isOn: $indexTasks)
                    Toggle("Files", isOn: $indexFiles)
                }
                
                Section {
                    Button("Reindex All Content") {
                        Task {
                            await SpotlightIndexer.shared.reindexAll()
                        }
                    }
                    
                    Button("Remove All from Spotlight", role: .destructive) {
                        Task {
                            await SpotlightIndexer.shared.removeAll()
                        }
                    }
                }
            }
        }
    }
}
```

### Indexing Implementation

```swift
class SpotlightIndexer {
    func indexThought(_ thought: ThoughtEntity) async {
        guard UserDefaults.standard.bool(forKey: "spotlight.enabled"),
              UserDefaults.standard.bool(forKey: "spotlight.indexThoughts") else {
            return
        }
        
        let attributeSet = CSSearchableItemAttributeSet(contentType: .text)
        attributeSet.title = String(thought.content.prefix(100))
        attributeSet.contentDescription = thought.content
        attributeSet.keywords = thought.tags
        attributeSet.contentCreationDate = thought.createdAt
        
        let item = CSSearchableItem(
            uniqueIdentifier: thought.id.uuidString,
            domainIdentifier: "com.kiro.thought",
            attributeSet: attributeSet
        )
        
        try? await CSSearchableIndex.default().indexSearchableItems([item])
    }
}
```

**Why**: Spotlight search is system-wide. Users may not want their thoughts or tasks appearing in search results on a shared device.

---

## Rule 10: Rate Limiting for Notifications

**Requirement**: Maximum **10 announced notifications per hour** to prevent notification spam.

### Rate Limiter Implementation

```swift
actor NotificationRateLimiter {
    private var announcementTimestamps: [Date] = []
    private let maxPerHour = 10
    
    func canAnnounce() -> Bool {
        let oneHourAgo = Date().addingTimeInterval(-3600)
        
        // Remove timestamps older than 1 hour
        announcementTimestamps.removeAll { $0 < oneHourAgo }
        
        return announcementTimestamps.count < maxPerHour
    }
    
    func recordAnnouncement() {
        announcementTimestamps.append(Date())
    }
}

// Usage
class NotificationManager {
    private let rateLimiter = NotificationRateLimiter()
    
    func scheduleAnnouncedNotification(_ content: UNNotificationContent) async throws {
        guard await rateLimiter.canAnnounce() else {
            logger.warning("Announcement rate limit exceeded, sending silent notification")
            var silentContent = content
            silentContent.interruptionLevel = .passive
            // Send without announcement
            return
        }
        
        await rateLimiter.recordAnnouncement()
        // Send with announcement
    }
}
```

**Why**: Too many spoken notifications are annoying and erode user trust. Rate limiting prevents notification fatigue.

---

## Enforcement

### Code Review Checklist

- [ ] All API tokens stored in Keychain with `.whenUnlockedThisDeviceOnly`
- [ ] No sensitive data in Siri response dialogs
- [ ] Widget content redacted (no raw task titles > 40 chars)
- [ ] Announcement permission explicitly requested with explanation
- [ ] Background sync status visible in Settings
- [ ] Spotlight indexing user-controllable
- [ ] Rate limiter enforced for announced notifications
- [ ] App works fully offline (local Core Data)
- [ ] Intent `perform()` methods return within 500ms
- [ ] Data export functionality available

### Automated Tests

```swift
class PrivacyRulesTests: XCTestCase {
    func testAPITokenStoredInKeychain() async throws {
        // Rule 3
        let token = "test_token"
        try SecureStorage.shared.saveAPIToken(token)
        
        // Verify not in UserDefaults
        XCTAssertNil(UserDefaults.standard.string(forKey: "api_token"))
        
        // Verify retrievable from Keychain
        let retrieved = try SecureStorage.shared.getAPIToken()
        XCTAssertEqual(retrieved, token)
    }
    
    func testWidgetContentRedaction() async throws {
        // Rule 4
        let sensitiveTask = Task(title: "Reset AWS root password - key: ABC123")
        let widget = DailySummaryWidget()
        let entry = await widget.getEntry(for: sensitiveTask)
        
        XCTAssertEqual(entry.taskTitle, "🔒 Private Task")
    }
    
    func testRateLimitEnforced() async throws {
        // Rule 10
        let limiter = NotificationRateLimiter()
        
        // Send 10 announcements (should succeed)
        for _ in 0..<10 {
            XCTAssertTrue(await limiter.canAnnounce())
            await limiter.recordAnnouncement()
        }
        
        // 11th should fail
        XCTAssertFalse(await limiter.canAnnounce())
    }
}
```

---

## Compliance Summary

| Rule | Apple Guideline | GDPR Article | CCPA Section |
|------|----------------|--------------|--------------|
| Rule 1: On-Device Processing | App Review 2.5.13 | Art. 25 (Data Protection by Design) | §1798.100(b) |
| Rule 2: Siri Audio Privacy | App Review 5.1.1 | Art. 5(1)(c) (Data Minimization) | §1798.110 |
| Rule 3: Keychain Storage | Security Best Practices | Art. 32 (Security) | §1798.150 |
| Rule 4: Widget Minimization | WidgetKit Guidelines | Art. 5(1)(c) | §1798.100(b) |
| Rule 5: Announcement Opt-In | UNF Framework | Art. 7 (Consent) | §1798.120 |
| Rule 6: Sync Transparency | App Review 5.1.1 | Art. 13 (Information) | §1798.115 |
| Rule 7: Local-First | N/A | Art. 17 (Right to Erasure) | §1798.105 |
| Rule 8: Dialog Privacy | SiriKit Guidelines | Art. 5(1)(c) | §1798.110 |
| Rule 9: Spotlight Control | Core Spotlight | Art. 21 (Right to Object) | §1798.120 |
| Rule 10: Rate Limiting | Human Interface Guidelines | Art. 5(1)(c) | §1798.100(b) |

---

**Status**: ✅ Privacy Rules Defined  
**Next Action**: Implement in iOS app with automated test coverage
