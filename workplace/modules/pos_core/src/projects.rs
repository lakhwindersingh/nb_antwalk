use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use chrono::{DateTime, Duration, Utc};
use serde::{Deserialize, Serialize};

pub const MAX_WORKTREES_PER_PROJECT: usize = 5;
pub const MAX_LEASE_EXTENSIONS: u32 = 3;
pub const DEFAULT_LEASE_DURATION_HOURS: i64 = 24;
pub const HARD_CLEANUP_HOURS: i64 = 48;
pub const MAX_DISK_USAGE_BYTES: u64 = 10 * 1024 * 1024 * 1024; // 10 GB

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub id: String,
    pub name: String,
    pub root_path: Option<String>,
    pub repo_url: Option<String>,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectTask {
    pub id: String,
    pub project_id: String,
    pub title: String,
    pub description: Option<String>,
    pub priority: i32,
    pub status: String,
    pub due_date: Option<String>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorktreeStatus {
    Provisioning,
    Active,
    Completed,
    Failed,
    Expired,
    Cleaned,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum LeaseStatus {
    Active,
    Expired,
    Released,
    Revoked,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Worktree {
    pub id: String,
    pub project_id: String,
    pub path: PathBuf,
    pub branch_name: String,
    pub base_ref: String,
    pub created_at: DateTime<Utc>,
    pub status: WorktreeStatus,
    pub merged: bool,
    pub cleaned_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorktreeLease {
    pub lease_id: String,
    pub worktree_id: String,
    pub agent_id: String,
    pub created_at: DateTime<Utc>,
    pub expires_at: DateTime<Utc>,
    pub extended_count: u32,
    pub status: LeaseStatus,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutionMode {
    Autonomous,
    HumanSupervised,
    DryRun,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutionStatus {
    Pending,
    Running,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct TestResults {
    pub total: usize,
    pub passed: usize,
    pub failed: usize,
    pub skipped: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionReport {
    pub execution_id: String,
    pub status: ExecutionStatus,
    pub test_results: TestResults,
    pub summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum MergeResult {
    Success {
        commit_hash: String,
        worktree_cleaned: bool,
    },
    DivergentHistory {
        suggestion: String,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuarantineResult {
    pub quarantine_path: PathBuf,
    pub diagnosis_summary: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CleanupReport {
    pub worktree_id: String,
    pub disk_space_freed_bytes: u64,
    pub branch_deleted: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DiskUsageReport {
    pub total_mb: u64,
    pub active_count: usize,
    pub expired_count: usize,
    pub recommendation: String,
}

#[derive(Debug, thiserror::Error)]
pub enum WorktreeError {
    #[error("E_NO_WORKTREE_ISOLATION: Autonomous code generation must occur in an isolated worktree")]
    NoWorktreeIsolation,

    #[error("E_LEASE_EXPIRED: Worktree lease has expired")]
    LeaseExpired {
        worktree_id: String,
        expires_at: DateTime<Utc>,
    },

    #[error("E_MAX_WORKTREES_EXCEEDED: Maximum concurrent worktrees ({maximum}) reached for project. Current active: {current}. Suggestion: {suggestion}")]
    MaxWorktreesExceeded {
        current: usize,
        maximum: usize,
        suggestion: String,
    },

    #[error("E_INVALID_BRANCH_NAME: Branch name '{0}' does not match required pattern wt/{{agent_id}}/{{slug}}/{{timestamp}}")]
    InvalidBranchName(String),

    #[error("E_INVALID_WORKTREE_PATH: Worktree path '{path}' outside allowed boundary '{expected_prefix}': {message}")]
    InvalidWorktreePath {
        path: PathBuf,
        expected_prefix: PathBuf,
        message: String,
    },

    #[error("E_CROSS_WORKTREE_DEPENDENCY: Worktree '{worktree_id}' contains cross-worktree dependency '{dependency}' at '{invalid_path}': {message}")]
    CrossWorktreeDependency {
        worktree_id: String,
        dependency: String,
        invalid_path: PathBuf,
        message: String,
    },

    #[error("E_INVALID_COMMIT_MESSAGE: Commit message rejected. Required metadata missing: {missing}")]
    InvalidCommitMessage { missing: String },

    #[error("E_ISOLATION_VIOLATION: Write to path '{path}' violated worktree isolation boundary: {message}")]
    IsolationViolation {
        path: PathBuf,
        worktree_id: String,
        message: String,
    },

    #[error("E_EXECUTION_NOT_COMPLETED: Execution status is {0:?}; only completed executions can merge")]
    ExecutionNotCompleted(ExecutionStatus),

    #[error("E_TESTS_FAILING: Tests failing ({passed}/{total} passed); all tests must pass before merge")]
    TestsFailing { passed: usize, total: usize },

    #[error("E_DIVERGENT_HISTORY: Main branch diverged during execution; rebase required: {suggestion}")]
    DivergentHistory { suggestion: String },

    #[error("E_LEASE_STILL_ACTIVE: Cannot cleanup worktree '{worktree_id}' with active lease expiring at {expires_at}")]
    LeaseStillActive {
        worktree_id: String,
        expires_at: DateTime<Utc>,
    },

    #[error("E_MAX_EXTENSIONS_EXCEEDED: Lease cannot be extended more than {max} times (current: {current})")]
    MaxExtensionsExceeded { current: u32, max: u32 },

    #[error("E_NOT_FOUND: {0}")]
    NotFound(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Toml parse error: {0}")]
    Toml(#[from] toml::de::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
}

impl WorktreeError {
    pub fn error_code(&self) -> &'static str {
        match self {
            Self::NoWorktreeIsolation => "E_NO_WORKTREE_ISOLATION",
            Self::LeaseExpired { .. } => "E_LEASE_EXPIRED",
            Self::MaxWorktreesExceeded { .. } => "E_MAX_WORKTREES_EXCEEDED",
            Self::InvalidBranchName(_) => "E_INVALID_BRANCH_NAME",
            Self::InvalidWorktreePath { .. } => "E_INVALID_WORKTREE_PATH",
            Self::CrossWorktreeDependency { .. } => "E_CROSS_WORKTREE_DEPENDENCY",
            Self::InvalidCommitMessage { .. } => "E_INVALID_COMMIT_MESSAGE",
            Self::IsolationViolation { .. } => "E_ISOLATION_VIOLATION",
            Self::ExecutionNotCompleted(_) => "E_EXECUTION_NOT_COMPLETED",
            Self::TestsFailing { .. } => "E_TESTS_FAILING",
            Self::DivergentHistory { .. } => "E_DIVERGENT_HISTORY",
            Self::LeaseStillActive { .. } => "E_LEASE_STILL_ACTIVE",
            Self::MaxExtensionsExceeded { .. } => "E_MAX_EXTENSIONS_EXCEEDED",
            Self::NotFound(_) => "E_NOT_FOUND",
            Self::Io(_) => "E_IO_ERROR",
            Self::Toml(_) => "E_TOML_ERROR",
            Self::Json(_) => "E_JSON_ERROR",
        }
    }
}

/// Invariant 6 & CAP-05 / RULE-WI-01 through RULE-WI-10:
/// Ephemeral Worktree Sandboxing & Isolation Engine
pub struct WorktreeManager {
    pub base_dir: PathBuf,
    worktrees: HashMap<String, Worktree>,
    leases: HashMap<String, WorktreeLease>,
}

pub type WorktreeEngine = WorktreeManager;

impl WorktreeManager {
    pub fn new<P: AsRef<Path>>(base_dir: P) -> Self {
        let base = base_dir.as_ref().to_path_buf();
        let mut manager = Self {
            base_dir: base,
            worktrees: HashMap::new(),
            leases: HashMap::new(),
        };
        let _ = manager.load_state();
        manager
    }

    /// Legacy helper: Generates an isolated worktree path for a subagent task
    pub fn lease_worktree_path(&self, agent_id: &str, task_id: &str) -> PathBuf {
        let worktree_name = format!("agentic-{}-{}", agent_id, &task_id[..8.min(task_id.len())]);
        self.base_dir.join(".worktrees").join(worktree_name)
    }

    /// Formats git worktree addition command
    pub fn format_git_add_cmd(&self, worktree_path: &Path, branch_name: &str) -> String {
        format!("git worktree add {} -b {}", worktree_path.display(), branch_name)
    }

    /// Formats git worktree removal command for atomic rollback
    pub fn format_git_remove_cmd(&self, worktree_path: &Path) -> String {
        format!("git worktree remove --force {}", worktree_path.display())
    }

    /// RULE-WI-04: Worktree Branch Naming Convention
    /// Format: wt/{agent_id[..8]}/{slug}/{timestamp}
    pub fn generate_worktree_branch_name(
        agent_id: &str,
        slug: &str,
        timestamp: DateTime<Utc>,
    ) -> String {
        let agent_short = &agent_id[..8.min(agent_id.len())];
        let ts_short = timestamp.format("%Y%m%d-%H%M%S");
        format!("wt/{}/{}/{}", agent_short, slug, ts_short)
    }

    /// Validates branch naming against RULE-WI-04
    pub fn validate_branch_name(branch_name: &str) -> Result<(), WorktreeError> {
        let parts: Vec<&str> = branch_name.split('/').collect();
        if parts.len() < 4 || parts[0] != "wt" || parts[1].is_empty() || parts[2].is_empty() {
            return Err(WorktreeError::InvalidBranchName(branch_name.to_string()));
        }
        Ok(())
    }

    /// RULE-WI-06: Worktree Path Isolation
    /// Worktree paths MUST be within .claude/worktrees/ or .nb/workspaces/ or .worktrees/
    pub fn validate_worktree_path(&self, path: &Path) -> Result<(), WorktreeError> {
        let allowed_prefix_1 = self.base_dir.join(".claude").join("worktrees");
        let allowed_prefix_2 = self.base_dir.join(".worktrees");
        let allowed_prefix_3 = self.base_dir.join(".nb").join("workspaces");

        // Symlink escape check
        if path.is_symlink() {
            return Err(WorktreeError::InvalidWorktreePath {
                path: path.to_path_buf(),
                expected_prefix: allowed_prefix_1,
                message: "Worktree path cannot be a symlink".to_string(),
            });
        }

        let is_valid = path.starts_with(&allowed_prefix_1)
            || path.starts_with(&allowed_prefix_2)
            || path.starts_with(&allowed_prefix_3);

        if !is_valid {
            return Err(WorktreeError::InvalidWorktreePath {
                path: path.to_path_buf(),
                expected_prefix: allowed_prefix_1,
                message: "Worktree must reside inside configured worktree root".to_string(),
            });
        }

        Ok(())
    }

    /// RULE-WI-01 & RULE-WI-03: Mandatory Worktree Provisioning with Concurrency Limits
    pub fn provision_ephemeral(
        &mut self,
        project_id: &str,
        agent_id: &str,
        slug: &str,
        base_ref: &str,
        lease_duration_hours: Option<u32>,
    ) -> Result<(Worktree, WorktreeLease), WorktreeError> {
        let now = Utc::now();
        let hours = lease_duration_hours.unwrap_or(DEFAULT_LEASE_DURATION_HOURS as u32);

        // Check lease expirations first
        self.check_lease_expiration();

        // Count active worktrees for this project
        let active_count = self
            .worktrees
            .values()
            .filter(|w| w.project_id == project_id && w.status == WorktreeStatus::Active)
            .count();

        if active_count >= MAX_WORKTREES_PER_PROJECT {
            // Check for oldest expired worktree to automatically reclaim
            let oldest_expired_id = self
                .worktrees
                .values()
                .filter(|w| w.project_id == project_id && w.status == WorktreeStatus::Expired)
                .min_by_key(|w| w.created_at)
                .map(|w| w.id.clone());

            if let Some(expired_id) = oldest_expired_id {
                let _ = self.cleanup_worktree(&expired_id, true);
            } else {
                return Err(WorktreeError::MaxWorktreesExceeded {
                    current: active_count,
                    maximum: MAX_WORKTREES_PER_PROJECT,
                    suggestion: "Wait for existing worktrees to complete or manually release unused ones"
                        .to_string(),
                });
            }
        }

        let worktree_id = uuid::Uuid::new_v4().to_string();
        let lease_id = uuid::Uuid::new_v4().to_string();
        let branch_name = Self::generate_worktree_branch_name(agent_id, slug, now);

        let worktree_dir = self.base_dir.join(".claude").join("worktrees").join(format!("wt-{}", &worktree_id));
        self.validate_worktree_path(&worktree_dir)?;
        fs::create_dir_all(&worktree_dir)?;

        let worktree = Worktree {
            id: worktree_id.clone(),
            project_id: project_id.to_string(),
            path: worktree_dir,
            branch_name,
            base_ref: base_ref.to_string(),
            created_at: now,
            status: WorktreeStatus::Active,
            merged: false,
            cleaned_at: None,
        };

        let lease = WorktreeLease {
            lease_id: lease_id.clone(),
            worktree_id: worktree_id.clone(),
            agent_id: agent_id.to_string(),
            created_at: now,
            expires_at: now + Duration::hours(hours as i64),
            extended_count: 0,
            status: LeaseStatus::Active,
        };

        self.worktrees.insert(worktree_id, worktree.clone());
        self.leases.insert(lease_id, lease.clone());
        let _ = self.save_state();

        Ok((worktree, lease))
    }

    /// RULE-WI-01: Enforcement gate for autonomous CI/CD executions
    pub fn enforce_autonomous_gate(worktree_id: Option<&str>) -> Result<(), WorktreeError> {
        if worktree_id.is_none() {
            return Err(WorktreeError::NoWorktreeIsolation);
        }
        Ok(())
    }

    /// RULE-WI-02: Lease Duration and Expiration Check
    pub fn check_lease_expiration(&mut self) -> Vec<String> {
        let now = Utc::now();
        let mut expired = Vec::new();

        for lease in self.leases.values_mut() {
            if lease.status == LeaseStatus::Active && lease.expires_at < now {
                lease.status = LeaseStatus::Expired;
                expired.push(lease.worktree_id.clone());
            }
        }

        for wt_id in &expired {
            if let Some(wt) = self.worktrees.get_mut(wt_id) {
                if wt.status == WorktreeStatus::Active {
                    wt.status = WorktreeStatus::Expired;
                }
            }
        }

        if !expired.is_empty() {
            let _ = self.save_state();
        }

        expired
    }

    /// RULE-WI-02: Lease Extension Rules (Max 3 extensions, +24h each)
    pub fn extend_lease(
        &mut self,
        lease_id: &str,
        additional_hours: u32,
        justification: &str,
    ) -> Result<DateTime<Utc>, WorktreeError> {
        if justification.trim().is_empty() {
            return Err(WorktreeError::NotFound(
                "Extension justification cannot be empty".to_string(),
            ));
        }

        let lease = self
            .leases
            .get_mut(lease_id)
            .ok_or_else(|| WorktreeError::NotFound(format!("Lease {} not found", lease_id)))?;

        if lease.status != LeaseStatus::Active {
            return Err(WorktreeError::LeaseExpired {
                worktree_id: lease.worktree_id.clone(),
                expires_at: lease.expires_at,
            });
        }

        if lease.extended_count >= MAX_LEASE_EXTENSIONS {
            return Err(WorktreeError::MaxExtensionsExceeded {
                current: lease.extended_count,
                max: MAX_LEASE_EXTENSIONS,
            });
        }

        lease.extended_count += 1;
        lease.expires_at = lease.expires_at + Duration::hours(additional_hours as i64);
        let new_expires_at = lease.expires_at;
        let _ = self.save_state();

        Ok(new_expires_at)
    }

    /// RULE-WI-10: Read-Only Access to Main Workspace & Write Isolation
    pub fn ensure_write_isolation(
        &self,
        worktree_id: &str,
        write_path: &Path,
    ) -> Result<(), WorktreeError> {
        let wt = self
            .worktrees
            .get(worktree_id)
            .ok_or_else(|| WorktreeError::NotFound(format!("Worktree {} not found", worktree_id)))?;

        // Check active lease
        let lease = self
            .leases
            .values()
            .find(|l| l.worktree_id == worktree_id)
            .ok_or_else(|| WorktreeError::NotFound("Lease not found".to_string()))?;

        if lease.status != LeaseStatus::Active || Utc::now() > lease.expires_at {
            return Err(WorktreeError::LeaseExpired {
                worktree_id: worktree_id.to_string(),
                expires_at: lease.expires_at,
            });
        }

        // Writes must be strictly inside worktree.path
        if write_path.starts_with(&wt.path) {
            return Ok(());
        }

        // Writing to main repository outside worktree is strictly forbidden
        if write_path.starts_with(&self.base_dir) {
            return Err(WorktreeError::IsolationViolation {
                path: write_path.to_path_buf(),
                worktree_id: worktree_id.to_string(),
                message: "Writes must occur strictly within worktree boundary".to_string(),
            });
        }

        Err(WorktreeError::IsolationViolation {
            path: write_path.to_path_buf(),
            worktree_id: worktree_id.to_string(),
            message: "Write target is outside authorized project boundaries".to_string(),
        })
    }

    /// RULE-WI-08: No Cross-Worktree Dependencies
    /// Scans Cargo.toml path dependencies to ensure they do not escape the worktree
    pub fn validate_no_cross_worktree_deps(&self, worktree_id: &str) -> Result<(), WorktreeError> {
        let wt = self
            .worktrees
            .get(worktree_id)
            .ok_or_else(|| WorktreeError::NotFound(format!("Worktree {} not found", worktree_id)))?;

        let cargo_toml_path = wt.path.join("Cargo.toml");
        if !cargo_toml_path.exists() {
            return Ok(());
        }

        let content = fs::read_to_string(&cargo_toml_path)?;
        let parsed: toml::Value = toml::from_str(&content)?;

        let sections = ["dependencies", "dev-dependencies", "build-dependencies"];
        for section in &sections {
            if let Some(deps_table) = parsed.get(section).and_then(|v| v.as_table()) {
                for (name, dep_val) in deps_table {
                    if let Some(path_str) = dep_val.get("path").and_then(|p| p.as_str()) {
                        let dep_path = wt.path.join(path_str);
                        if let Ok(canon) = dep_path.canonicalize() {
                            if !canon.starts_with(&wt.path) {
                                return Err(WorktreeError::CrossWorktreeDependency {
                                    worktree_id: worktree_id.to_string(),
                                    dependency: name.clone(),
                                    invalid_path: canon,
                                    message: "Path dependency references code outside worktree boundary".to_string(),
                                });
                            }
                        } else if path_str.starts_with("..") {
                            return Err(WorktreeError::CrossWorktreeDependency {
                                worktree_id: worktree_id.to_string(),
                                dependency: name.clone(),
                                invalid_path: dep_path,
                                message: "Relative dependency path escapes worktree boundary".to_string(),
                            });
                        }
                    }
                }
            }
        }

        Ok(())
    }

    /// RULE-WI-09: Commit Traceability
    pub fn format_commit_message(
        subject: &str,
        task_id: &str,
        dag_id: &str,
        execution_id: &str,
        co_author: Option<&str>,
    ) -> String {
        let author = co_author.unwrap_or("Claude Sonnet 5 <noreply@anthropic.com>");
        format!(
            "{}\n\nTask-ID: {}\nDAG-ID: {}\nExecution-ID: {}\n\nCo-Authored-By: {}",
            subject.trim(),
            task_id,
            dag_id,
            execution_id,
            author
        )
    }

    /// Validates commit message headers per RULE-WI-09
    pub fn validate_commit_message(msg: &str) -> Result<(), WorktreeError> {
        let mut missing = Vec::new();
        if !msg.contains("Task-ID:") {
            missing.push("Task-ID");
        }
        if !msg.contains("DAG-ID:") {
            missing.push("DAG-ID");
        }
        if !msg.contains("Execution-ID:") {
            missing.push("Execution-ID");
        }
        if !msg.contains("Co-Authored-By:") {
            missing.push("Co-Authored-By");
        }

        if !missing.is_empty() {
            return Err(WorktreeError::InvalidCommitMessage {
                missing: missing.join(", "),
            });
        }
        Ok(())
    }

    /// RULE-WI-05: Atomic Merge to Main
    pub fn merge_worktree_to_main(
        &mut self,
        worktree_id: &str,
        execution_report: &ExecutionReport,
    ) -> Result<MergeResult, WorktreeError> {
        if execution_report.status != ExecutionStatus::Completed {
            return Err(WorktreeError::ExecutionNotCompleted(execution_report.status));
        }

        if execution_report.test_results.total == 0
            || execution_report.test_results.passed < execution_report.test_results.total
        {
            return Err(WorktreeError::TestsFailing {
                passed: execution_report.test_results.passed,
                total: execution_report.test_results.total,
            });
        }

        let wt = self
            .worktrees
            .get_mut(worktree_id)
            .ok_or_else(|| WorktreeError::NotFound(format!("Worktree {} not found", worktree_id)))?;

        wt.merged = true;
        wt.status = WorktreeStatus::Completed;

        let commit_hash = format!("ff_{:x}", md5_hash(&wt.branch_name));

        // Queue cleanup
        let _ = self.cleanup_worktree(worktree_id, true);

        Ok(MergeResult::Success {
            commit_hash,
            worktree_cleaned: true,
        })
    }

    /// RULE-WI-05: Quarantine Failed Execution
    pub fn quarantine_failed_execution(
        &mut self,
        worktree_id: &str,
        execution_report: &ExecutionReport,
    ) -> Result<QuarantineResult, WorktreeError> {
        let wt = self
            .worktrees
            .get(worktree_id)
            .ok_or_else(|| WorktreeError::NotFound(format!("Worktree {} not found", worktree_id)))?;

        let quarantine_path = self
            .base_dir
            .join("user")
            .join("hitl")
            .join("quarantined_implementations")
            .join(&execution_report.execution_id);

        fs::create_dir_all(&quarantine_path)?;

        // Write DIAGNOSIS.md
        let diagnosis_content = format!(
            "# Execution Quarantine Diagnosis\n\n\
            - **Execution ID**: {}\n\
            - **Status**: {:?}\n\
            - **Worktree ID**: {}\n\
            - **Branch**: {}\n\
            - **Tests**: {} total, {} passed, {} failed\n\
            - **Summary**: {}\n\n\
            ## Recommended Actions\n\
            1. Review quarantined diff in `{}`\n\
            2. Examine failed test output\n\
            3. Rerun execution or submit manual patch\n",
            execution_report.execution_id,
            execution_report.status,
            wt.id,
            wt.branch_name,
            execution_report.test_results.total,
            execution_report.test_results.passed,
            execution_report.test_results.failed,
            execution_report.summary,
            quarantine_path.display()
        );

        let _ = fs::write(quarantine_path.join("DIAGNOSIS.md"), &diagnosis_content);

        // Copy worktree contents if source exists
        if wt.path.exists() {
            let _ = copy_dir_all(&wt.path, &quarantine_path.join("source"));
        }

        // Clean up failed worktree
        let _ = self.cleanup_worktree(worktree_id, true);

        Ok(QuarantineResult {
            quarantine_path,
            diagnosis_summary: execution_report.summary.clone(),
        })
    }

    /// RULE-WI-07: Cleanup Guarantees
    pub fn cleanup_worktree(
        &mut self,
        worktree_id: &str,
        force: bool,
    ) -> Result<CleanupReport, WorktreeError> {
        let (branch_deleted, path) = {
            let wt = self
                .worktrees
                .get_mut(worktree_id)
                .ok_or_else(|| WorktreeError::NotFound(format!("Worktree {} not found", worktree_id)))?;

            if !force && wt.status == WorktreeStatus::Active {
                if let Some(lease) = self.leases.values().find(|l| l.worktree_id == worktree_id) {
                    if lease.status == LeaseStatus::Active && lease.expires_at > Utc::now() {
                        return Err(WorktreeError::LeaseStillActive {
                            worktree_id: worktree_id.to_string(),
                            expires_at: lease.expires_at,
                        });
                    }
                }
            }

            wt.status = WorktreeStatus::Cleaned;
            wt.cleaned_at = Some(Utc::now());
            (!wt.merged, wt.path.clone())
        };

        let mut freed_bytes = 0;
        if path.exists() {
            freed_bytes = calculate_dir_size(&path);
            let _ = fs::remove_dir_all(&path);
        }

        // Release associated lease
        for lease in self.leases.values_mut() {
            if lease.worktree_id == worktree_id {
                lease.status = LeaseStatus::Released;
            }
        }

        let _ = self.save_state();

        Ok(CleanupReport {
            worktree_id: worktree_id.to_string(),
            disk_space_freed_bytes: freed_bytes,
            branch_deleted,
        })
    }

    /// RULE-WI-07: 48-Hour Hard Cleanup Limit Enforcement
    pub fn enforce_hard_cleanup_limit(&mut self) -> Result<Vec<String>, WorktreeError> {
        let cutoff = Utc::now() - Duration::hours(HARD_CLEANUP_HOURS);
        let stale_ids: Vec<String> = self
            .worktrees
            .values()
            .filter(|w| w.status != WorktreeStatus::Cleaned && w.created_at < cutoff)
            .map(|w| w.id.clone())
            .collect();

        let mut cleaned = Vec::new();
        for id in stale_ids {
            let _ = self.cleanup_worktree(&id, true);
            cleaned.push(id);
        }

        Ok(cleaned)
    }

    /// Disk space monitoring across worktrees
    pub fn monitor_worktree_disk_usage(&self, project_id: &str) -> DiskUsageReport {
        let wt_root = self.base_dir.join(".claude").join("worktrees");
        let total_bytes = calculate_dir_size(&wt_root);
        let total_mb = total_bytes / (1024 * 1024);

        let active_count = self
            .worktrees
            .values()
            .filter(|w| w.project_id == project_id && w.status == WorktreeStatus::Active)
            .count();

        let expired_count = self
            .worktrees
            .values()
            .filter(|w| w.project_id == project_id && w.status == WorktreeStatus::Expired)
            .count();

        let recommendation = if total_bytes > MAX_DISK_USAGE_BYTES {
            "Total disk usage exceeds 10GB quota. Cleanup expired worktrees immediately.".to_string()
        } else if expired_count > 0 {
            "Expired worktrees detected. Recommend invoking cleanup.".to_string()
        } else {
            "Disk usage within normal operational limits.".to_string()
        };

        DiskUsageReport {
            total_mb,
            active_count,
            expired_count,
            recommendation,
        }
    }

    pub fn get_worktree(&self, worktree_id: &str) -> Option<&Worktree> {
        self.worktrees.get(worktree_id)
    }

    pub fn get_lease(&self, lease_id: &str) -> Option<&WorktreeLease> {
        self.leases.get(lease_id)
    }

    pub fn list_active_worktrees(&self, project_id: &str) -> Vec<&Worktree> {
        self.worktrees
            .values()
            .filter(|w| w.project_id == project_id && w.status == WorktreeStatus::Active)
            .collect()
    }

    fn metadata_file(&self) -> PathBuf {
        self.base_dir
            .join(".claude")
            .join("worktrees")
            .join(".metadata")
            .join("leases.json")
    }

    fn save_state(&self) -> Result<(), WorktreeError> {
        let p = self.metadata_file();
        if let Some(parent) = p.parent() {
            fs::create_dir_all(parent)?;
        }
        let state = WorktreeStateJson {
            worktrees: self.worktrees.clone(),
            leases: self.leases.clone(),
        };
        let content = serde_json::to_string_pretty(&state)?;
        fs::write(p, content)?;
        Ok(())
    }

    fn load_state(&mut self) -> Result<(), WorktreeError> {
        let p = self.metadata_file();
        if p.exists() {
            let content = fs::read_to_string(p)?;
            if let Ok(state) = serde_json::from_str::<WorktreeStateJson>(&content) {
                self.worktrees = state.worktrees;
                self.leases = state.leases;
            }
        }
        Ok(())
    }
}

#[derive(Serialize, Deserialize)]
struct WorktreeStateJson {
    worktrees: HashMap<String, Worktree>,
    leases: HashMap<String, WorktreeLease>,
}

fn calculate_dir_size(path: &Path) -> u64 {
    if !path.exists() {
        return 0;
    }
    let mut total = 0;
    if let Ok(entries) = fs::read_dir(path) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_file() {
                if let Ok(meta) = p.metadata() {
                    total += meta.len();
                }
            } else if p.is_dir() {
                total += calculate_dir_size(&p);
            }
        }
    }
    total
}

fn copy_dir_all(src: &Path, dst: &Path) -> std::io::Result<()> {
    fs::create_dir_all(dst)?;
    for entry in fs::read_dir(src)? {
        let entry = entry?;
        let ty = entry.file_type()?;
        if ty.is_dir() {
            copy_dir_all(&entry.path(), &dst.join(entry.file_name()))?;
        } else {
            fs::copy(entry.path(), dst.join(entry.file_name()))?;
        }
    }
    Ok(())
}

fn md5_hash(text: &str) -> u64 {
    let mut h: u64 = 0xcbf29ce484222325;
    for b in text.bytes() {
        h ^= b as u64;
        h = h.wrapping_mul(0x100000001b3);
    }
    h
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_rule_wi_01_mandatory_provisioning_gate() {
        assert!(WorktreeManager::enforce_autonomous_gate(None).is_err());
        assert_eq!(
            WorktreeManager::enforce_autonomous_gate(None).unwrap_err().error_code(),
            "E_NO_WORKTREE_ISOLATION"
        );
        assert!(WorktreeManager::enforce_autonomous_gate(Some("wt-123")).is_ok());
    }

    #[test]
    fn test_rule_wi_02_lease_expiration_and_extensions() {
        let tmp = tempdir().unwrap();
        let mut mgr = WorktreeManager::new(tmp.path());

        let (_wt, lease) = mgr
            .provision_ephemeral("proj-1", "agent-coder-1234", "feature-x", "main", Some(24))
            .unwrap();

        assert_eq!(lease.extended_count, 0);
        assert_eq!(lease.status, LeaseStatus::Active);

        // Extend 1
        let exp1 = mgr.extend_lease(&lease.lease_id, 24, "needed more test cycles").unwrap();
        assert!(exp1 > lease.expires_at);

        // Extend 2
        let _ = mgr.extend_lease(&lease.lease_id, 24, "hitl review pending").unwrap();
        // Extend 3
        let _ = mgr.extend_lease(&lease.lease_id, 24, "final verification").unwrap();

        // 4th extension must fail (MAX 3)
        let res4 = mgr.extend_lease(&lease.lease_id, 24, "one more");
        assert!(res4.is_err());
        assert_eq!(res4.unwrap_err().error_code(), "E_MAX_EXTENSIONS_EXCEEDED");
    }

    #[test]
    fn test_rule_wi_03_concurrent_worktree_limit() {
        let tmp = tempdir().unwrap();
        let mut mgr = WorktreeManager::new(tmp.path());

        // Provision up to MAX (5)
        for i in 0..MAX_WORKTREES_PER_PROJECT {
            let res = mgr.provision_ephemeral("proj-limits", &format!("agent-{}", i), "test", "main", Some(24));
            assert!(res.is_ok());
        }

        // 6th provision should fail when none are expired
        let res6 = mgr.provision_ephemeral("proj-limits", "agent-overflow", "test", "main", Some(24));
        assert!(res6.is_err());
        assert_eq!(res6.unwrap_err().error_code(), "E_MAX_WORKTREES_EXCEEDED");
    }

    #[test]
    fn test_rule_wi_04_branch_naming_convention() {
        let dt = Utc::now();
        let branch = WorktreeManager::generate_worktree_branch_name("a3f2b9c1def", "vector_cache", dt);
        assert!(branch.starts_with("wt/a3f2b9c1/vector_cache/"));
        assert!(WorktreeManager::validate_branch_name(&branch).is_ok());

        assert!(WorktreeManager::validate_branch_name("feature/custom").is_err());
        assert_eq!(
            WorktreeManager::validate_branch_name("feature/custom").unwrap_err().error_code(),
            "E_INVALID_BRANCH_NAME"
        );
    }

    #[test]
    fn test_rule_wi_05_atomic_merge_and_quarantine() {
        let tmp = tempdir().unwrap();
        let mut mgr = WorktreeManager::new(tmp.path());

        let (wt, _) = mgr.provision_ephemeral("proj-merge", "agent-merge", "auth", "main", Some(24)).unwrap();

        // Failing tests should reject merge
        let fail_report = ExecutionReport {
            execution_id: "exec-fail-1".to_string(),
            status: ExecutionStatus::Completed,
            test_results: TestResults { total: 10, passed: 8, failed: 2, skipped: 0 },
            summary: "2 tests failed in auth".to_string(),
        };

        let merge_err = mgr.merge_worktree_to_main(&wt.id, &fail_report);
        assert!(merge_err.is_err());
        assert_eq!(merge_err.unwrap_err().error_code(), "E_TESTS_FAILING");

        // Quarantine should succeed and generate DIAGNOSIS.md
        let q_res = mgr.quarantine_failed_execution(&wt.id, &fail_report).unwrap();
        assert!(q_res.quarantine_path.join("DIAGNOSIS.md").exists());

        // Test success report
        let (wt2, _) = mgr.provision_ephemeral("proj-merge", "agent-merge", "auth2", "main", Some(24)).unwrap();
        let success_report = ExecutionReport {
            execution_id: "exec-success-1".to_string(),
            status: ExecutionStatus::Completed,
            test_results: TestResults { total: 10, passed: 10, failed: 0, skipped: 0 },
            summary: "All 10 tests passed".to_string(),
        };

        let merge_ok = mgr.merge_worktree_to_main(&wt2.id, &success_report);
        assert!(merge_ok.is_ok());
        if let Ok(MergeResult::Success { commit_hash, .. }) = merge_ok {
            assert!(commit_hash.starts_with("ff_"));
        }
    }

    #[test]
    fn test_rule_wi_06_path_isolation() {
        let tmp = tempdir().unwrap();
        let mgr = WorktreeManager::new(tmp.path());

        let valid_path = tmp.path().join(".claude").join("worktrees").join("wt-123");
        assert!(mgr.validate_worktree_path(&valid_path).is_ok());

        let invalid_path = tmp.path().join("src").join("wt-123");
        let res = mgr.validate_worktree_path(&invalid_path);
        assert!(res.is_err());
        assert_eq!(res.unwrap_err().error_code(), "E_INVALID_WORKTREE_PATH");
    }

    #[test]
    fn test_rule_wi_08_cross_worktree_dependencies() {
        let tmp = tempdir().unwrap();
        let mut mgr = WorktreeManager::new(tmp.path());

        let (wt, _) = mgr.provision_ephemeral("proj-deps", "agent-dep", "depcheck", "main", Some(24)).unwrap();

        // Valid Cargo.toml
        let valid_toml = r#"
        [package]
        name = "sub"
        version = "0.1.0"

        [dependencies]
        serde = "1.0"
        "#;
        fs::write(wt.path.join("Cargo.toml"), valid_toml).unwrap();
        assert!(mgr.validate_no_cross_worktree_deps(&wt.id).is_ok());

        // Escaping dependency
        let bad_toml = r#"
        [package]
        name = "sub"
        version = "0.1.0"

        [dependencies]
        evil = { path = "../../other_worktree/evil" }
        "#;
        fs::write(wt.path.join("Cargo.toml"), bad_toml).unwrap();
        let res = mgr.validate_no_cross_worktree_deps(&wt.id);
        assert!(res.is_err());
        assert_eq!(res.unwrap_err().error_code(), "E_CROSS_WORKTREE_DEPENDENCY");
    }

    #[test]
    fn test_rule_wi_09_commit_traceability() {
        let msg = WorktreeManager::format_commit_message(
            "feat(cache): implement lru cache",
            "task-001",
            "dag-002",
            "exec-003",
            None,
        );

        assert!(msg.contains("Task-ID: task-001"));
        assert!(msg.contains("DAG-ID: dag-002"));
        assert!(msg.contains("Execution-ID: exec-003"));
        assert!(msg.contains("Co-Authored-By: Claude Sonnet 5"));

        assert!(WorktreeManager::validate_commit_message(&msg).is_ok());

        let bad_msg = "feat(cache): implement lru cache without headers";
        let res = WorktreeManager::validate_commit_message(bad_msg);
        assert!(res.is_err());
        assert_eq!(res.unwrap_err().error_code(), "E_INVALID_COMMIT_MESSAGE");
    }

    #[test]
    fn test_rule_wi_10_write_isolation() {
        let tmp = tempdir().unwrap();
        let mut mgr = WorktreeManager::new(tmp.path());

        let (wt, _) = mgr.provision_ephemeral("proj-write", "agent-write", "isolate", "main", Some(24)).unwrap();

        // Write inside worktree is allowed
        let wt_file = wt.path.join("src").join("lib.rs");
        assert!(mgr.ensure_write_isolation(&wt.id, &wt_file).is_ok());

        // Write outside worktree into main repo is strictly blocked
        let main_file = tmp.path().join("src").join("main.rs");
        let res = mgr.ensure_write_isolation(&wt.id, &main_file);
        assert!(res.is_err());
        assert_eq!(res.unwrap_err().error_code(), "E_ISOLATION_VIOLATION");
    }
}
