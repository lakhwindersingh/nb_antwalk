pub mod storage;
pub mod vault;
pub mod privacy;
pub mod projects;
pub mod thoughts;
pub mod activities;
pub mod finance;
pub mod merkle;

pub use storage::{Database, StorageError};
pub use vault::{SecretBuffer, LeaseToken, VaultManager};
pub use privacy::RedactionSentinel;
pub use projects::{Project, ProjectTask, WorktreeManager};
pub use thoughts::{Thought, ThoughtType};
pub use activities::{Activity, Habit, StreakCalculator};
pub use finance::{Transaction, TransactionStatus, HitlFinancialGate};
pub use merkle::MerkleBlockHeader;

pub type Result<T> = std::result::Result<T, Box<dyn std::error::Error + Send + Sync>>;
