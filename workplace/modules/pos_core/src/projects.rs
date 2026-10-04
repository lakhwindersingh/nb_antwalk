use std::path::{Path, PathBuf};
use serde::{Deserialize, Serialize};

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

/// Invariant 6 & CAP-05: Ephemeral Worktree Sandboxing
/// Provisions isolated Git worktree workspaces for subagents to test and build changes
pub struct WorktreeManager {
    base_dir: PathBuf,
}

impl WorktreeManager {
    pub fn new<P: AsRef<Path>>(base_dir: P) -> Self {
        Self {
            base_dir: base_dir.as_ref().to_path_buf(),
        }
    }

    /// Generates an isolated worktree path for a subagent task
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
}
