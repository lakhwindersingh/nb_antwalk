pub mod storage;
pub mod vault;
pub mod privacy;
pub mod projects;
pub mod thoughts;
pub mod activities;
pub mod finance;
pub mod merkle;
pub mod sandbox;
pub mod write_coordinator;
pub mod disaster_recovery;

pub use storage::{Database, StorageError};
pub use vault::{SecretBuffer, LeaseToken, VaultManager};
pub use privacy::RedactionSentinel;
pub use projects::{
    CleanupReport, DiskUsageReport, ExecutionMode, ExecutionReport, ExecutionStatus, LeaseStatus,
    MergeResult, Project, ProjectTask, QuarantineResult, TestResults, Worktree, WorktreeEngine,
    WorktreeError, WorktreeLease, WorktreeManager, WorktreeStatus,
};
pub use thoughts::{Thought, ThoughtType};
pub use activities::{Activity, Habit, StreakCalculator};
pub use finance::{Transaction, TransactionStatus, HitlFinancialGate};
pub use merkle::MerkleBlockHeader;
pub use sandbox::{SandboxPolicy, SandboxValidator, SandboxViolation};
pub use write_coordinator::{
    CoordinatorMetrics, PrioritizedWrite, WriteCoordinator, WritePriority, WriteRequest,
};
pub use disaster_recovery::{
    Bip39Recovery, DisasterRecoveryError, PaperBackupDocument, SecretShare, ShamirSecretSharing,
};

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;
