# Worktree Isolation Rules

**Version**: 1.0.0  
**Status**: Foundation  
**Scope**: Thought-to-Project extension - ephemeral worktree management

## Purpose

This document defines inviolable rules for managing ephemeral git worktrees during
autonomous code generation. Worktrees provide isolation boundaries that prevent
partial implementations from polluting the main workspace and enable safe concurrent
development by multiple agents.

## Core Principles

1. **Isolation First**: All autonomous code generation MUST occur in ephemeral worktrees, never in the main workspace
2. **Lease-Based Lifecycle**: Worktrees have time-bounded leases with automatic expiration
3. **Atomic Merge**: Worktree content merges to main only when all tests pass
4. **Clean Failure**: Failed implementations are quarantined, not merged
5. **Resource Limits**: Maximum concurrent worktrees per project to prevent disk exhaustion

## Worktree Lifecycle Rules

### RULE-WI-01: Mandatory Worktree Provisioning

**Rule**: Before any code generation begins, agent_autonomous_coder MUST provision
an ephemeral worktree via the `provision_ephemeral_worktree` wire contract method.

**Enforcement**:
```rust
pub fn execute_autonomous_cicd(
    dag_id: &str,
    execution_mode: ExecutionMode,
    worktree_id: Option<String>,
) -> Result<ExecutionReport, ExecutionError> {
    // If no worktree_id provided, must provision one
    let worktree = match worktree_id {
        Some(id) => WorktreeEngine::get_existing(id)?,
        None => WorktreeEngine::provision_ephemeral(
            project_id,
            format!("cicd-{}", dag_id),
            "main",
            24, // lease_duration_hours
        )?,
    };
    
    // Verify worktree_path before ANY file writes
    assert!(worktree.path.starts_with(".claude/worktrees/"));
    assert!(worktree.path.exists());
    
    // All subsequent file operations must use worktree.path as root
    std::env::set_current_dir(&worktree.path)?;
    
    // ... rest of execution
}
```

**Violation Consequences**:
- Execution fails immediately with `E_NO_WORKTREE_ISOLATION`
- No code generation proceeds
- Prevents accidental modification of main workspace

### RULE-WI-02: Lease Duration and Expiration

**Rule**: Every worktree has a maximum lease duration (default: 24 hours). Upon
expiration, the worktree is automatically marked for cleanup unless explicitly extended.

**Lease Management**:
```rust
pub struct WorktreeLease {
    lease_id: String,        // uuid
    worktree_id: String,     // uuid
    agent_id: String,        // Which agent holds the lease
    created_at: DateTime,
    expires_at: DateTime,
    extended_count: u32,     // Track extensions (max 3)
    status: LeaseStatus,     // Active, Expired, Released
}

pub enum LeaseStatus {
    Active,
    Expired,       // Auto-expired after duration
    Released,      // Agent explicitly released
    Revoked,       // Admin forced revocation
}

pub fn check_lease_expiration() {
    let now = Utc::now();
    for lease in WorktreeLease::all_active() {
        if lease.expires_at < now {
            // Mark as expired
            lease.status = LeaseStatus::Expired;
            lease.save();
            
            // Queue for cleanup (grace period: 1 hour)
            CleanupQueue::enqueue(lease.worktree_id, now + Duration::hours(1));
            
            // Notify agent if still running
            if let Some(agent) = Agent::get_running(lease.agent_id) {
                agent.notify(WorktreeEvent::LeaseExpired { 
                    worktree_id: lease.worktree_id.clone(),
                    grace_period_hours: 1,
                });
            }
        }
    }
}
```

**Lease Extension Rules**:
- Maximum 3 extensions per lease
- Each extension adds 24 hours
- Must provide justification for extension
- Extensions require active agent request (not automatic)

**Violation Consequences**:
- Expired worktrees become read-only after grace period
- Automatic cleanup after 1-hour grace period
- Agent receives `E_LEASE_EXPIRED` on next file write

### RULE-WI-03: Concurrent Worktree Limits

**Rule**: Maximum 5 concurrent active worktrees per project to prevent disk exhaustion
and resource contention.

**Enforcement**:
```rust
pub const MAX_WORKTREES_PER_PROJECT: usize = 5;

pub fn provision_ephemeral(
    project_id: &str,
    branch_name: String,
    base_ref: &str,
    lease_duration_hours: u32,
) -> Result<Worktree, ProvisionError> {
    // Count active worktrees for this project
    let active_count = Worktree::count_active(project_id)?;
    
    if active_count >= MAX_WORKTREES_PER_PROJECT {
        // Find oldest expired worktree to clean
        if let Some(expired_wt) = Worktree::find_expired(project_id) {
            WorktreeEngine::cleanup_worktree(expired_wt.id)?;
        } else {
            return Err(ProvisionError::TooManyWorktrees {
                current: active_count,
                maximum: MAX_WORKTREES_PER_PROJECT,
                suggestion: "Wait for existing worktrees to complete or manually release unused ones",
            });
        }
    }
    
    // Proceed with provisioning
    // ...
}
```

**Concurrent Worktree Scenarios**:
- ✅ **Allowed**: 3 agents implementing different plans concurrently (3 worktrees)
- ✅ **Allowed**: 1 main implementation + 2 experimental branches (3 worktrees)
- ❌ **Blocked**: Attempting to create 6th worktree without cleanup
- ✅ **Allowed**: Auto-cleanup of expired worktree to make room for new one

**Violation Consequences**:
- Provisioning fails with `E_MAX_WORKTREES_EXCEEDED`
- Agent must wait for cleanup or manually release worktrees
- User notified to review stalled executions

### RULE-WI-04: Worktree Branch Naming Convention

**Rule**: Worktree branches MUST follow naming convention: `wt/{agent_id}/{slug}/{timestamp}`

**Branch Naming**:
```rust
pub fn generate_worktree_branch_name(
    agent_id: &str,
    slug: &str,  // From plan or execution context
    timestamp: DateTime,
) -> String {
    let agent_short = &agent_id[..8];  // First 8 chars of agent ID
    let ts_short = timestamp.format("%Y%m%d-%H%M%S");
    format!("wt/{}/{}/{}", agent_short, slug, ts_short)
}

// Example: wt/a3f2b9c1/vector_cache/20261004-142300
```

**Benefits**:
- Clear identification of worktree branches in `git branch -a`
- Easy cleanup of stale worktree branches
- Prevents collision with user branches
- Enables audit trail of autonomous executions

**Cleanup Strategy**:
```bash
# List all worktree branches older than 7 days
git branch -a | grep '^wt/' | while read branch; do
    last_commit=$(git log -1 --format=%ct $branch)
    age_days=$(( ($(date +%s) - $last_commit) / 86400 ))
    if [ $age_days -gt 7 ]; then
        echo "Stale worktree branch: $branch (age: $age_days days)"
        # Optionally: git branch -D $branch
    fi
done
```

**Violation Consequences**:
- Provisioning warning if non-standard branch name used
- Cleanup scripts may not detect worktree branches
- Manual intervention required for orphaned branches

### RULE-WI-05: Atomic Merge or Full Rollback

**Rule**: When autonomous execution completes, worktree content must either:
1. Merge to main atomically (all tests pass, fast-forward merge), OR
2. Be fully quarantined (failed execution, preserved for review)

No partial merges allowed.

**Merge Workflow**:
```rust
pub fn merge_worktree_to_main(
    worktree: &Worktree,
    execution_report: &ExecutionReport,
) -> Result<MergeResult, MergeError> {
    // Pre-merge validation
    if execution_report.status != ExecutionStatus::Completed {
        return Err(MergeError::ExecutionNotCompleted {
            status: execution_report.status,
            message: "Only completed executions can merge",
        });
    }
    
    if execution_report.test_results.passed < execution_report.test_results.total {
        return Err(MergeError::TestsFailing {
            passed: execution_report.test_results.passed,
            total: execution_report.test_results.total,
            message: "All tests must pass before merge",
        });
    }
    
    // Switch to main workspace
    let main_repo = Repository::open(project_root)?;
    main_repo.checkout("main")?;
    
    // Attempt fast-forward merge
    let worktree_branch = &worktree.branch_name;
    let merge_result = main_repo.merge_ff(worktree_branch)?;
    
    if !merge_result.is_fast_forward {
        // Main branch diverged during execution
        return Err(MergeError::DivergentHistory {
            suggestion: "Rebase worktree onto latest main and retry",
        });
    }
    
    // Success - mark worktree for cleanup
    worktree.mark_merged()?;
    CleanupQueue::enqueue_immediate(worktree.id);
    
    Ok(MergeResult::Success {
        commit_hash: merge_result.head_commit,
        worktree_cleaned: false,  // Queued for async cleanup
    })
}
```

**Rollback Strategy**:
```rust
pub fn quarantine_failed_execution(
    worktree: &Worktree,
    execution_report: &ExecutionReport,
) -> Result<QuarantineResult, QuarantineError> {
    let quarantine_path = format!(
        "user/hitl/quarantined_implementations/{}/",
        execution_report.execution_id
    );
    
    // Copy worktree contents to quarantine
    fs::create_dir_all(&quarantine_path)?;
    copy_dir_recursive(&worktree.path, &quarantine_path)?;
    
    // Generate diagnosis report
    let diagnosis = DiagnosisReport::generate(execution_report);
    fs::write(
        format!("{}/DIAGNOSIS.md", quarantine_path),
        diagnosis.to_markdown(),
    )?;
    
    // Cleanup worktree (failed branch not preserved)
    WorktreeEngine::cleanup_worktree(worktree.id)?;
    
    Ok(QuarantineResult {
        quarantine_path,
        diagnosis_summary: diagnosis.summary,
    })
}
```

**Violation Consequences**:
- No cherry-picking of "good" commits from failed execution
- No manual merge of worktree branches (use workflow commands)
- Prevents inconsistent state in main branch

### RULE-WI-06: Worktree Path Isolation

**Rule**: Worktree paths MUST be within `.claude/worktrees/` directory at project root.
No worktrees outside this boundary.

**Path Validation**:
```rust
pub fn validate_worktree_path(path: &Path) -> Result<(), PathError> {
    let canonical = path.canonicalize()?;
    let expected_prefix = project_root().join(".claude/worktrees");
    
    if !canonical.starts_with(&expected_prefix) {
        return Err(PathError::OutsideBoundary {
            path: canonical,
            expected_prefix,
            message: "Worktree must be within .claude/worktrees/",
        });
    }
    
    // Additional check: no symlink escapes
    if path.read_link().is_ok() {
        return Err(PathError::SymlinkNotAllowed {
            path: path.to_path_buf(),
            message: "Worktree path cannot be a symlink",
        });
    }
    
    Ok(())
}
```

**Directory Structure**:
```
.claude/worktrees/
├── wt-a3f2b9c1-4d5e-6f78/   # Worktree for execution exec-a3f2b9c1
│   ├── .git                  # Git worktree metadata
│   ├── workplace/            # Source code
│   ├── Cargo.toml
│   └── ...
├── wt-f9a3c2b1-7d8e-4f56/   # Another concurrent worktree
│   └── ...
└── .metadata/                # Worktree lease tracking
    ├── leases.db
    └── cleanup_queue.json
```

**Violation Consequences**:
- Provisioning fails with `E_INVALID_WORKTREE_PATH`
- Prevents accidental modification of files outside project
- Security boundary enforcement

### RULE-WI-07: Cleanup Guarantees

**Rule**: Every provisioned worktree MUST be cleaned up within 48 hours of creation,
regardless of execution status.

**Cleanup Triggers**:
1. **Success**: Immediate cleanup after merge to main
2. **Failure**: Immediate cleanup after quarantine
3. **Expiration**: 1-hour grace period, then auto-cleanup
4. **Forced**: Admin manual cleanup command
5. **Timeout**: 48-hour hard limit (even if lease extended)

**Cleanup Implementation**:
```rust
pub fn cleanup_worktree(worktree_id: &str) -> Result<CleanupReport, CleanupError> {
    let worktree = Worktree::get(worktree_id)?;
    
    // 1. Verify worktree is eligible for cleanup
    if worktree.status == WorktreeStatus::Active {
        let lease = WorktreeLease::get_for_worktree(worktree_id)?;
        if lease.status == LeaseStatus::Active && lease.expires_at > Utc::now() {
            return Err(CleanupError::LeaseStillActive {
                worktree_id: worktree_id.to_string(),
                expires_at: lease.expires_at,
                message: "Cannot cleanup worktree with active lease",
            });
        }
    }
    
    // 2. Remove git worktree
    let repo = Repository::open(project_root)?;
    repo.worktree_prune(&worktree.path, None)?;
    
    // 3. Delete filesystem directory
    if worktree.path.exists() {
        fs::remove_dir_all(&worktree.path)?;
    }
    
    // 4. Delete worktree branch (if not merged)
    if !worktree.merged {
        let branch_ref = format!("refs/heads/{}", worktree.branch_name);
        repo.find_reference(&branch_ref)?.delete()?;
    }
    
    // 5. Release lease
    if let Ok(lease) = WorktreeLease::get_for_worktree(worktree_id) {
        lease.release()?;
    }
    
    // 6. Mark worktree as cleaned
    worktree.status = WorktreeStatus::Cleaned;
    worktree.cleaned_at = Some(Utc::now());
    worktree.save()?;
    
    Ok(CleanupReport {
        worktree_id: worktree_id.to_string(),
        disk_space_freed_mb: calculate_disk_usage(&worktree.path)?,
        branch_deleted: !worktree.merged,
    })
}
```

**48-Hour Hard Limit**:
```rust
pub fn enforce_hard_cleanup_limit() {
    let cutoff = Utc::now() - Duration::hours(48);
    for worktree in Worktree::all_active() {
        if worktree.created_at < cutoff {
            warn!(
                "Worktree {} exceeded 48-hour limit, forcing cleanup",
                worktree.id
            );
            // Force cleanup regardless of lease status
            WorktreeEngine::cleanup_worktree_force(worktree.id).ok();
        }
    }
}
```

**Violation Consequences**:
- Disk space accumulation (prevented by automatic enforcement)
- Stale worktrees consume inode quota
- Periodic cleanup job runs every 6 hours

### RULE-WI-08: No Cross-Worktree Dependencies

**Rule**: Code in one worktree MUST NOT depend on code in another concurrent worktree.
Each worktree is a complete, self-contained workspace.

**Enforcement**:
```rust
pub fn validate_no_cross_worktree_deps(worktree: &Worktree) -> Result<(), DepError> {
    // Check Cargo.toml for path dependencies
    let cargo_toml = fs::read_to_string(worktree.path.join("Cargo.toml"))?;
    let manifest: CargoManifest = toml::from_str(&cargo_toml)?;
    
    for (name, dep) in &manifest.dependencies {
        if let Some(path) = dep.path.as_ref() {
            let dep_path = worktree.path.join(path).canonicalize()?;
            
            // Ensure dependency path is within this worktree
            if !dep_path.starts_with(&worktree.path) {
                return Err(DepError::CrossWorktreeDependency {
                    worktree_id: worktree.id.clone(),
                    dependency: name.clone(),
                    invalid_path: dep_path,
                    message: "Dependencies must be within worktree boundary",
                });
            }
        }
    }
    
    Ok(())
}
```

**Why This Matters**:
- Worktrees have independent lifecycles (one may be cleaned while another active)
- Prevents build failures due to missing dependencies
- Ensures reproducibility (worktree can be archived and rebuilt standalone)

**Violation Consequences**:
- Compilation failure when dependency worktree is cleaned
- Execution quarantined with `E_CROSS_WORKTREE_DEPENDENCY`
- Plan decomposition must ensure self-contained components

### RULE-WI-09: Commit Traceability

**Rule**: Every commit in a worktree MUST include execution metadata in the commit message:
- `Task-ID`: uuid of the task from the DAG
- `DAG-ID`: uuid of the task DAG
- `Execution-ID`: uuid of the autonomous execution
- `Co-Authored-By`: Claude Sonnet 5 attribution

**Commit Message Template**:
```
feat(storage): Implement vector cache with LRU eviction

Implements in-memory LRU cache for vector embeddings with
configurable capacity and O(1) get/put operations.

Task-ID: task-c8f9a2b1-3d4e-5f67-8901-23456789abcd
DAG-ID: dag-f3a9b2c1-4d5e-6f78-9012-3456789abcde
Execution-ID: exec-a3f2b9c1-4d5e-6f78-9012-3456789abcde

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

**Enforcement**:
```rust
pub fn create_task_commit(
    worktree: &Worktree,
    task: &Task,
    execution_id: &str,
) -> Result<String, CommitError> {
    let repo = Repository::open(&worktree.path)?;
    
    // Build commit message
    let message = format!(
        "{}\n\nTask-ID: {}\nDAG-ID: {}\nExecution-ID: {}\n\nCo-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>",
        task.commit_subject,
        task.task_id,
        task.dag_id,
        execution_id,
    );
    
    // Create commit
    let oid = repo.commit_all(&message)?;
    
    Ok(oid.to_string())
}
```

**Benefits**:
- Bidirectional traceability: commit → task → DAG → plan → MVS → thought
- Audit trail for autonomous code generation
- Easy rollback of specific task implementations
- Knowledge loop closure linking

**Violation Consequences**:
- Commit rejected by pre-commit hook
- Execution quarantined with `E_INVALID_COMMIT_MESSAGE`
- Manual commits in worktrees are not allowed

### RULE-WI-10: Read-Only Access to Main Workspace

**Rule**: While a worktree is active, the agent MAY read from the main workspace
(e.g., to reference existing code) but MUST NOT write to it.

**Enforcement**:
```rust
pub fn ensure_write_isolation(path: &Path, worktree: &Worktree) -> Result<(), IsolationError> {
    let canonical = path.canonicalize()?;
    
    // Check if path is within worktree
    if canonical.starts_with(&worktree.path) {
        // Write allowed
        return Ok(());
    }
    
    // Check if path is in main workspace
    if canonical.starts_with(project_root()) {
        return Err(IsolationError::WriteToMainWorkspace {
            path: canonical,
            worktree_id: worktree.id.clone(),
            message: "Writes must occur within worktree boundary",
        });
    }
    
    Ok(())
}
```

**Read Access Allowed**:
- Reference existing implementations for pattern matching
- Read shared configuration files (Cargo.toml, .cargo/config.toml)
- Access project-level documentation

**Write Access Forbidden**:
- Modifying source files in main workspace
- Creating new files outside worktree
- Updating shared configuration

**Violation Consequences**:
- File write fails with `E_ISOLATION_VIOLATION`
- Execution quarantined
- Agent must retry within worktree boundary

## Worktree Metadata Schema

```rust
pub struct Worktree {
    pub id: String,              // uuid
    pub project_id: String,      // Which project this belongs to
    pub path: PathBuf,           // .claude/worktrees/wt-{id}/
    pub branch_name: String,     // wt/{agent_id}/{slug}/{timestamp}
    pub base_ref: String,        // Branched from (usually "main")
    pub created_at: DateTime,
    pub status: WorktreeStatus,
    pub merged: bool,            // True if successfully merged to main
    pub cleaned_at: Option<DateTime>,
}

pub enum WorktreeStatus {
    Provisioning,    // Being created
    Active,          // Agent is working in it
    Completed,       // Execution finished, pending merge
    Failed,          // Execution failed, pending quarantine
    Expired,         // Lease expired
    Cleaned,         // Removed from disk
}

pub struct WorktreeLease {
    pub lease_id: String,
    pub worktree_id: String,
    pub agent_id: String,
    pub created_at: DateTime,
    pub expires_at: DateTime,
    pub extended_count: u32,
    pub status: LeaseStatus,
}
```

## Performance Considerations

### Disk Space Management

**Target**: Keep total worktree disk usage under 10GB per project

**Monitoring**:
```rust
pub fn monitor_worktree_disk_usage(project_id: &str) -> DiskUsageReport {
    let worktrees_path = project_root().join(".claude/worktrees");
    let total_usage = calculate_dir_size(&worktrees_path);
    
    let active_worktrees = Worktree::all_active_for_project(project_id);
    let expired_worktrees = Worktree::all_expired_for_project(project_id);
    
    DiskUsageReport {
        total_mb: total_usage / 1_048_576,
        active_count: active_worktrees.len(),
        expired_count: expired_worktrees.len(),
        recommendation: if total_usage > 10_737_418_240 {
            "Cleanup expired worktrees to free disk space"
        } else {
            "Disk usage within normal range"
        },
    }
}
```

### Git Performance

**Consideration**: Large worktree count can slow `git status` and `git branch` operations.

**Mitigation**:
- Periodic cleanup of merged/expired worktree branches
- Use `git worktree prune` to clean up stale worktree metadata
- Keep active worktree count ≤ 5 per project

## Related Documents

- `agent_autonomous_coder.yaml` - Agent configuration with worktree execution details
- `wf_plan_to_cicd.yaml` - Workflow orchestration of worktree lifecycle
- `thought_to_project_wire_contracts.yaml` - Wire contract method: provision_ephemeral_worktree
- `plan_derivation_invariants.md` - Plan-level invariants that apply before worktree provisioning

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-04 | Initial worktree isolation rules for autonomous CI/CD |
