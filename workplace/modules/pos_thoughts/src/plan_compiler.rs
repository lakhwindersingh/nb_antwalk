use crate::mvs_synthesis::MvsSpecification;
use crate::task_dag::{PipelineTask, TaskDag};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CompiledPlan {
    pub plan_id: String,
    pub domain_slug: String,
    pub title: String,
    pub concise_markdown: String,
    pub tasks: Vec<PipelineTask>,
}

/// Domain Layer Plan Generator per custom_domain_layer_template.md (E-THOUGHT-04)
pub struct PlanCompiler;

impl PlanCompiler {
    pub fn compile(mvs: &MvsSpecification) -> CompiledPlan {
        let plan_id = format!("domain_{}", mvs.domain_slug);

        let mut markdown = String::new();
        markdown.push_str("---\n");
        markdown.push_str("plan_type: \"layerable_domain_plan\"\n");
        markdown.push_str(&format!("plan_id: \"{}\"\n", plan_id));
        markdown.push_str(&format!("name: \"{}\"\n", mvs.title));
        markdown.push_str("status: \"compiled_ready_for_execution\"\n");
        markdown.push_str("---\n\n");

        markdown.push_str(&format!("# Domain Plan: {}\n\n", mvs.title));
        markdown.push_str("### Executive Summary\n");
        markdown.push_str(&format!(
            "Auto-synthesized layerable domain specification derived from Thought `{}` (Confidence: {:.2}).\n\n",
            mvs.thought_id, mvs.confidence_score
        ));

        markdown.push_str("### Components & Contracts\n");
        for comp in &mvs.components {
            markdown.push_str(&format!("- **`{}`**: {}\n", comp.name, comp.description));
            markdown.push_str(&format!("  - Contract: `{}`\n", comp.interface_spec));
        }

        markdown.push_str("\n### System Constraints & Invariants\n");
        for c in &mvs.constraints {
            markdown.push_str(&format!("- **{}** ({}): {}\n", c.constraint_type, c.severity, c.description));
        }

        // Generate task blueprints
        let mut tasks = Vec::new();
        for (i, comp) in mvs.components.iter().enumerate() {
            tasks.push(PipelineTask {
                task_id: format!("task-{}-{:02}", mvs.domain_slug, i + 1),
                name: format!("Implement {}", comp.name),
                description: format!("Develop and test {}", comp.description),
                priority: (i + 1) as i32,
                estimated_minutes: 45,
            });
        }

        CompiledPlan {
            plan_id,
            domain_slug: mvs.domain_slug.clone(),
            title: mvs.title.clone(),
            concise_markdown: markdown,
            tasks,
        }
    }

    /// Converts compiled tasks into a ready-to-run TaskDag
    pub fn build_dag(plan: &CompiledPlan) -> TaskDag {
        let mut dag = TaskDag::new();
        let mut prev_id: Option<String> = None;

        for task in &plan.tasks {
            dag.add_task(task.clone());
            if let Some(ref p_id) = prev_id {
                let _ = dag.add_dependency(&task.task_id, p_id);
            }
            prev_id = Some(task.task_id.clone());
        }

        dag
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::mvs_synthesis::{MvsComponent, MvsConstraint};
    use chrono::Utc;

    #[test]
    fn test_plan_compilation() {
        let mvs = MvsSpecification {
            mvs_id: "mvs-123".to_string(),
            thought_id: "thought-abc".to_string(),
            title: "Distributed Lock".to_string(),
            domain_slug: "dist_lock".to_string(),
            components: vec![MvsComponent {
                name: "RedlockBackend".to_string(),
                description: "Redis Redlock adapter".to_string(),
                interface_spec: "pub trait LockBackend".to_string(),
                target_tests: vec!["test_lock_ttl".to_string()],
            }],
            constraints: vec![MvsConstraint {
                constraint_type: "Safety".to_string(),
                description: "Lock tokens must be UUIDv4".to_string(),
                severity: "MustHave".to_string(),
            }],
            confidence_score: 0.92,
            created_at: Utc::now(),
        };

        let plan = PlanCompiler::compile(&mvs);
        assert_eq!(plan.plan_id, "domain_dist_lock");
        assert!(plan.concise_markdown.contains("RedlockBackend"));
        assert_eq!(plan.tasks.len(), 1);

        let dag = PlanCompiler::build_dag(&plan);
        assert_eq!(dag.task_count(), 1);
        let sorted = dag.topological_sort().unwrap();
        assert_eq!(sorted[0].name, "Implement RedlockBackend");
    }
}
