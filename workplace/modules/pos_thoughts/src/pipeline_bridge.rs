use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use pos_core::projects::WorktreeManager;
use crate::mvs_synthesis::{MvsSpecification, MvsSynthesizer};
use crate::plan_compiler::{CompiledPlan, PlanCompiler};

#[derive(Debug, thiserror::Error)]
pub enum PipelineBridgeError {
    #[error("E_PIPELINE_NOT_ACTIONABLE: Thought is not actionable enough (score: {score:.2} < 0.65)")]
    NotActionable { score: f64 },

    #[error("E_PIPELINE_TOO_AMBIGUOUS: Ambiguity entropy {entropy:.2} exceeds threshold 0.40; RFC generated")]
    TooAmbiguous { entropy: f64 },

    #[error("E_PIPELINE_MVS_ERROR: {0}")]
    MvsError(#[from] crate::mvs_synthesis::MvsSynthesisError),

    #[error("E_PIPELINE_DAG_ERROR: {0}")]
    DagError(#[from] crate::task_dag::TaskDagError),

    #[error("E_PIPELINE_WORKTREE_ERROR: {0}")]
    WorktreeError(#[from] pos_core::projects::WorktreeError),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PipelineExecutionResult {
    pub pipeline_id: String,
    pub thought_id: String,
    pub mvs_spec: MvsSpecification,
    pub compiled_plan: CompiledPlan,
    pub worktree_id: String,
    pub branch_name: String,
    pub worktree_path: String,
    pub status: String,
    pub closed_loop_backlink: String,
    pub timestamp: DateTime<Utc>,
}

/// End-to-End Thought-to-Project Autonomous Pipeline Bridge (E-THOUGHT-07 & E-THOUGHT-08)
pub struct ThoughtToProjectBridge {
    pub synthesizer: MvsSynthesizer,
}

impl Default for ThoughtToProjectBridge {
    fn default() -> Self {
        Self {
            synthesizer: MvsSynthesizer::default(),
        }
    }
}

impl ThoughtToProjectBridge {
    pub fn new() -> Self {
        Self::default()
    }

    /// Executes the full pipeline from raw thought note to isolated worktree & plan
    pub fn execute_pipeline(
        &self,
        thought_id: &str,
        title: &str,
        domain_slug: &str,
        content: &str,
        actionability_score: f64,
        ambiguity_entropy: f64,
        worktree_mgr: &mut WorktreeManager,
    ) -> Result<PipelineExecutionResult, PipelineBridgeError> {
        // 1. Actionability Gate
        if actionability_score < 0.65 {
            return Err(PipelineBridgeError::NotActionable {
                score: actionability_score,
            });
        }

        // 2. Ambiguity Entropy Gate
        if ambiguity_entropy > 0.40 {
            return Err(PipelineBridgeError::TooAmbiguous {
                entropy: ambiguity_entropy,
            });
        }

        // 3. MVS Derivation (E-THOUGHT-02)
        let mvs_spec = self.synthesizer.derive_mvs(
            thought_id,
            title,
            domain_slug,
            content,
            actionability_score,
        )?;

        // 4. Plan Compilation (E-THOUGHT-04)
        let compiled_plan = PlanCompiler::compile(&mvs_spec);

        // 5. Task DAG Decomposition (E-THOUGHT-05)
        let dag = PlanCompiler::build_dag(&compiled_plan);
        let _sorted_tasks = dag.topological_sort()?;

        // 6. Ephemeral Worktree Provisioning (E-THOUGHT-06 / CAP-05)
        let (worktree, _lease) = worktree_mgr.provision_ephemeral(
            &format!("project-{}", domain_slug),
            "agent_thought_synthesizer",
            domain_slug,
            "main",
            Some(24),
        )?;

        // 7. Bidirectional Knowledge Loop Closure (E-THOUGHT-08)
        let pipeline_id = format!("pipe_{}_{}", domain_slug, Utc::now().timestamp());
        let backlink = format!(
            "<!-- Backlink: Percipience Autonomous Pipeline Sealed -->\n\
            - **Pipeline ID**: `{}`\n\
            - **Branch**: `{}`\n\
            - **Plan**: `{}`\n\
            - **Status**: Worktree Provisioned, Ready for Autonomous Coder",
            pipeline_id, worktree.branch_name, compiled_plan.plan_id
        );

        Ok(PipelineExecutionResult {
            pipeline_id,
            thought_id: thought_id.to_string(),
            mvs_spec,
            compiled_plan,
            worktree_id: worktree.id,
            branch_name: worktree.branch_name,
            worktree_path: worktree.path.to_string_lossy().to_string(),
            status: "WORKTREE_PROVISIONED".to_string(),
            closed_loop_backlink: backlink,
            timestamp: Utc::now(),
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_full_thought_to_project_pipeline_flow() {
        let tmp = tempdir().unwrap();
        let mut worktree_mgr = WorktreeManager::new(tmp.path());
        let bridge = ThoughtToProjectBridge::new();

        let raw_thought = r#"
        # Authentication Micro-Module
        ## Component: TokenValidator
        Validates JWT bearer tokens and claims
        - Constraint: Must reject expired tokens with 401
        "#;

        let res = bridge.execute_pipeline(
            "thought-99",
            "Auth Micro-Module",
            "auth_module",
            raw_thought,
            0.85, // S >= 0.65
            0.15, // E <= 0.40
            &mut worktree_mgr,
        );

        assert!(res.is_ok());
        let output = res.unwrap();
        assert_eq!(output.thought_id, "thought-99");
        assert_eq!(output.status, "WORKTREE_PROVISIONED");
        assert!(output.branch_name.contains("auth_module"));
        assert!(output.closed_loop_backlink.contains("Pipeline ID"));
    }

    #[test]
    fn test_pipeline_ambiguity_block() {
        let tmp = tempdir().unwrap();
        let mut worktree_mgr = WorktreeManager::new(tmp.path());
        let bridge = ThoughtToProjectBridge::new();

        let res = bridge.execute_pipeline(
            "thought-vague",
            "Vague Idea",
            "vague",
            "something vague",
            0.85,
            0.55, // E > 0.40 -> Must Block
            &mut worktree_mgr,
        );

        assert!(matches!(res, Err(PipelineBridgeError::TooAmbiguous { .. })));
    }
}
