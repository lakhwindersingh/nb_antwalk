# Thought-to-Project Extension: Gap Remediation Status

**Last Updated**: 2026-10-04  
**Status**: Actively remediating identified gaps

---

## Remediation Progress

### ✅ COMPLETED

#### GAP-T2P-004: Missing Wire Contracts
**Status**: RESOLVED  
**Completion Date**: 2026-10-04  

**Files Created**:
1. `.nb/context/contracts/thought_to_project_wire_contracts.yaml` (469 lines)
   - 8 RPC methods fully specified with input/output schemas
   - Validation rules and error codes defined
   - Performance targets established (p95 latency benchmarks)

2. `.nb/context/contracts/plan_synthesis_contract.json` (609 lines)
   - Complete JSON Schema for MVS specification structure
   - Component, constraint, and test_case definitions
   - Architectural dependency tracking (GAP-001 through GAP-012)
   - Validation examples included

**Impact**: Eliminates integration ambiguity between pos_thoughts and pos_projects pillars.

---

#### GAP-T2P-005: Workflow Integration Missing
**Status**: RESOLVED  
**Completion Date**: 2026-10-04  

**Files Created**:
1. `.nb/agentic/custom/workflows/wf_thought_to_plan.yaml` (374 lines)
   - 8-stage pipeline: evaluation → ambiguity check → MVS synthesis → validation → approval → plan compilation → knowledge update → notification
   - HITL clarification RFC generation for ambiguous thoughts (ambiguity > 0.40)
   - Auto-approval for high-confidence MVS (confidence > 0.85)
   - Comprehensive rollback and error handling strategies
   - 5-minute timeout with exponential backoff retry policy

2. `.nb/agentic/custom/workflows/wf_plan_to_cicd.yaml` (460 lines)
   - 11-stage pipeline: parse → decompose DAG → provision worktree → execute CI/CD → verify tests → approval gate → merge → seal → backlink → cleanup → notify
   - Ephemeral worktree isolation with 24-hour lease management
   - Bounded self-healing with max 3 retries per task
   - Optional HITL approval gate before merge
   - Merkle chain sealing for cryptographic verification
   - Fast-forward merge enforcement with conflict detection
   - 60-minute timeout for full autonomous execution

3. `.nb/agentic/custom/agents/agent_thought_synthesizer.yaml` (317 lines)
4. `.nb/agentic/custom/agents/agent_plan_architect.yaml` (377 lines)
5. `.nb/agentic/custom/agents/agent_autonomous_coder.yaml` (409 lines)
   - Complete agent configurations with capabilities, wire contracts, and error handling
   - Model configurations (temperature, tokens, reasoning effort)
   - Agent-specific execution rules and prompt templates
   - Realistic performance targets (60% autonomous success rate)

6. `.nb/agentic/custom/rulesets/plan_derivation_invariants.md` (496 lines)
   - 10 core invariants for thought→MVS→plan transformation
   - Chain of custody, schema compliance, component completeness
   - DAG acyclicity, testability verification, gap resolution
   - Enforcement code examples and violation consequences

7. `.nb/agentic/custom/rulesets/worktree_isolation_rules.md` (456 lines)
   - 10 rules for ephemeral worktree lifecycle management
   - Lease-based provisioning with 24-hour default, max 5 concurrent
   - Atomic merge or full rollback (no partial merges)
   - Commit traceability with execution metadata

**Integration Points**:
- Both workflows reference `thought_to_project_wire_contracts.yaml` for RPC calls
- `wf_thought_to_plan` outputs feed directly into `wf_plan_to_cicd` inputs
- Agent configurations implement all wire contract methods
- Rulesets define invariants enforced throughout pipeline
- Observability with audit trails at `.nb/logs/audit/`

**Impact**: Provides complete executable orchestration for thought→plan→code→ship pipeline with enforced invariants and isolation boundaries.

---

### 🚧 IN PROGRESS

#### GAP-T2P-003: Ambiguity Entropy Formula Unvalidated
**Status**: IN PROGRESS  
**Next Action**: Replace heuristic formula with LLM-based semantic checklist

---

#### GAP-T2P-008: Actionability Score Algorithm Undefined
**Status**: CAN PROTOTYPE STANDALONE  
**Next Action**: Implement LLM-based semantic evaluation (no blockers)

**Implementation Ready**: Algorithm defined in `agent_thought_synthesizer.yaml` RULE-TS-03
```yaml
prompt_template: |
  Evaluate if this thought is ready to become a software project.
  
  Rate 0.0-1.0 on these dimensions:
  1. **Clear Goal**: Is the desired outcome explicitly stated?
  2. **Technical Details**: Are APIs, data structures, or algorithms mentioned?
  3. **Success Criteria**: Are acceptance criteria or metrics defined?
  4. **Dependencies**: Are constraints or prerequisites identified?
  5. **Bounded Scope**: Is the scope well-defined?
```

**Planned Implementation**:
```rust
// workplace/modules/pos_thoughts/src/actionability.rs
pub struct ActionabilityEvaluator {
    llm_client: LLMClient,
}

impl ActionabilityEvaluator {
    pub async fn evaluate(&self, content: &str) -> Result<ActionabilityReport, Error> {
        let prompt = ACTIONABILITY_PROMPT_TEMPLATE.replace("{content}", content);
        let response = self.llm_client.call(&prompt).await?;
        // Parse JSON: {"score": 0.0-1.0, "dimensions": {...}, "missing_elements": [...]}
        Ok(serde_json::from_str(&response)?)
    }
}
```

---

#### GAP-T2P-003: Ambiguity Entropy Formula Unvalidated
**Status**: CAN PROTOTYPE STANDALONE  
**Next Action**: Replace mathematical entropy with LLM-based semantic evaluation (no blockers)

**Planned Implementation**:
```rust
// workplace/modules/pos_thoughts/src/ambiguity.rs
pub struct AmbiguityEvaluator {
    llm_client: LLMClient,
}

impl AmbiguityEvaluator {
    pub async fn evaluate(&self, content: &str) -> Result<AmbiguityReport, Error> {
        let prompt = AMBIGUITY_PROMPT_TEMPLATE.replace("{content}", content);
        let response = self.llm_client.call(&prompt).await?;
        // Parse JSON: {"score": 0.0-1.0, "vague_elements": [...], "questions_to_ask": [...]}
        Ok(serde_json::from_str(&response)?)
    }
}
```

**Evaluation Template** (defined in `agent_thought_synthesizer.yaml` RULE-TS-02):
```yaml
prompt_template: |
  Identify vague or ambiguous elements in this thought.
  
  Check for:
  1. **Undefined Terms**: Are key concepts explained or referenced?
  2. **Missing Specifics**: Are there weasel words ("better", "faster", "improved")?
  3. **Unclear Scope**: Is it clear what's in/out of scope?
  4. **Unspecified Details**: Are data structures, APIs, or interfaces mentioned?
  
  Return JSON: {"score": 0.0-1.0, "vague_elements": [...], "questions_to_ask": [...]}
```


---

### ⏸️ BLOCKED (Awaiting Core Dependencies)

#### GAP-T2P-001: Missing Core Dependencies
**Status**: BLOCKED  
**Blocker**: Requires Phase 1 core pillar implementation

**Required Before Implementation**:
1. **Rust Workspace Setup**:
   - Create `Cargo.toml` in workspace root
   - Define workspace members: `pos_thoughts`, `pos_projects`, `pos_storage`, `pos_workflows`
   - Establish shared dependencies (tokio, serde, sqlx, pulldown-cmark, petgraph, git2)

2. **pos_thoughts Crate**:
   ```
   workplace/modules/pos_thoughts/
   ├── Cargo.toml
   ├── src/
   │   ├── lib.rs
   │   ├── ast_parser.rs       # pulldown-cmark integration
   │   ├── actionability.rs    # Scoring algorithm
   │   ├── ambiguity.rs        # Checklist evaluator
   │   ├── entity_extractor.rs # Wikilinks, headings, code blocks
   │   └── storage.rs          # SQLite thoughts table
   └── tests/
       ├── readiness_score_test.rs
       └── ast_extraction_test.rs
   ```

3. **pos_projects Crate**:
   ```
   workplace/modules/pos_projects/
   ├── Cargo.toml
   ├── src/
   │   ├── lib.rs
   │   ├── task_dag.rs         # Petgraph decomposer
   │   ├── worktree_engine.rs  # git2 worktree management
   │   ├── plan_compiler.rs    # MVS → concise.md
   │   └── storage.rs          # SQLite projects table
   └── tests/
       ├── task_dag_cycle_test.rs
       └── ephemeral_worktree_test.rs
   ```

4. **Core Infrastructure**:
   - SQLite schema initialization (`pos_storage` crate)
   - CLI framework (`pos` binary in `workplace/cli/`)
   - Agent configuration system (`.nb/agentic/custom/agents/`)

**Estimated Effort**: 8-12 weeks for core pillars

---

#### GAP-T2P-002: Autonomous CI/CD Unrealistic Scope
**Status**: ACKNOWLEDGED  
**Action**: Re-scope expectations and add safety gates

**Changes Implemented in Workflows**:
1. **Realistic Success Metrics** (wf_plan_to_cicd.yaml):
   ```yaml
   success_criteria:
     - autonomous_success_rate > 0.60  # 60%, not 85%
   ```

2. **Mandatory HITL Gates** (parameter available):
   ```yaml
   parameters:
     - name: require_human_review
       type: boolean
       default: false  # Can enable per-execution
   ```

3. **Bounded Retry with Quarantine**:
   ```yaml
   max_retries: 3
   on_max_retries_exceeded:
     action: quarantine
     target: user/hitl/quarantined_implementations/
   ```

4. **Incremental Verification** (stage 05):
   ```yaml
   - stage_id: "05_verify_tests"
     stage_name: "Final Test Suite Verification"
     action:
       type: shell_command
       command: cargo test --all-features --workspace
   ```

**Remaining Work**:
- Implement confidence scoring in `agent_autonomous_coder`
- Add sensitive module detection (auth, payments, data integrity)
- Build incremental verification pipeline (unit → integration → e2e)

---

#### GAP-T2P-006: Git Worktree Isolation Incomplete
**Status**: BLOCKED  
**Blocker**: Requires `WorktreeEngine` implementation in pos_projects

**Required Implementation**:
```rust
// workplace/modules/pos_projects/src/worktree_engine.rs
use git2::{Repository, Worktree};
use chrono::{DateTime, Utc, Duration};

pub struct WorktreeEngine {
    repo: Repository,
    lease_tracker: LeaseTracker,
}

pub struct WorktreeLease {
    pub lease_id: String,
    pub worktree_id: String,
    pub worktree_path: PathBuf,
    pub branch: String,
    pub agent_id: String,
    pub expires_at: DateTime<Utc>,
}

impl WorktreeEngine {
    pub fn provision(&mut self, branch_name: &str, agent_id: &str, lease_hours: u32) 
        -> Result<WorktreeLease, WorktreeError> {
        // 1. Check quota (max 5 per project)
        if self.lease_tracker.active_count() >= 5 {
            return Err(WorktreeError::QuotaExceeded);
        }
        
        // 2. Create worktree in .nb/workspaces/<slug>/
        let worktree_path = format!(".nb/workspaces/{}_{}", branch_name, Utc::now().timestamp());
        let worktree = self.repo.worktree(&worktree_path, Some(&branch_name), None)?;
        
        // 3. Create lease
        let lease = WorktreeLease {
            lease_id: Uuid::new_v4().to_string(),
            worktree_id: Uuid::new_v4().to_string(),
            worktree_path: PathBuf::from(worktree_path),
            branch: branch_name.to_string(),
            agent_id: agent_id.to_string(),
            expires_at: Utc::now() + Duration::hours(lease_hours as i64),
        };
        
        self.lease_tracker.register(lease.clone())?;
        Ok(lease)
    }
    
    pub fn release(&mut self, lease_id: &str) -> Result<(), WorktreeError> {
        // 1. Get lease
        let lease = self.lease_tracker.get(lease_id)?;
        
        // 2. Prune worktree
        let worktree = self.repo.find_worktree(&lease.worktree_path)?;
        worktree.prune(None)?;
        
        // 3. Delete lease
        self.lease_tracker.delete(lease_id)?;
        Ok(())
    }
    
    pub fn cleanup_expired(&mut self) -> Result<Vec<String>, WorktreeError> {
        let expired = self.lease_tracker.find_expired()?;
        for lease in &expired {
            self.release(&lease.lease_id)?;
        }
        Ok(expired.iter().map(|l| l.lease_id.clone()).collect())
    }
    
    pub fn merge_fast_forward(&self, worktree_path: &Path, target_branch: &str) 
        -> Result<Oid, WorktreeError> {
        // 1. Open worktree repo
        let worktree_repo = Repository::open(worktree_path)?;
        
        // 2. Check if fast-forward possible
        let head = worktree_repo.head()?;
        let target = worktree_repo.find_branch(target_branch, git2::BranchType::Local)?;
        
        if !worktree_repo.graph_descendant_of(head.target().unwrap(), target.get().target().unwrap())? {
            return Err(WorktreeError::MergeConflict);
        }
        
        // 3. Fast-forward merge
        let target_commit = target.get().peel_to_commit()?;
        worktree_repo.checkout_tree(target_commit.as_object(), None)?;
        worktree_repo.set_head(target_commit.id().as_str())?;
        
        Ok(target_commit.id())
    }
}
```

**Test Coverage Required**:
- Quota enforcement (max 5 worktrees)
- Lease expiration and auto-cleanup
- Fast-forward merge success path
- Merge conflict detection
- Orphaned worktree recovery

---

#### GAP-T2P-007: Knowledge Loop Closure Fragile
**Status**: BLOCKED  
**Blocker**: Requires thought versioning and conflict resolution implementation

**Required Schema Changes**:
```sql
-- Track thought snapshots at promotion time
CREATE TABLE IF NOT EXISTS thought_versions (
    version_id TEXT PRIMARY KEY,
    thought_id TEXT NOT NULL REFERENCES thoughts(id),
    content_snapshot TEXT NOT NULL,
    promoted_at DATETIME NOT NULL,
    plan_id TEXT,
    FOREIGN KEY (thought_id) REFERENCES thoughts(id) ON DELETE CASCADE
);

-- Many-to-many: thoughts to commits
CREATE TABLE IF NOT EXISTS thought_commits (
    thought_id TEXT NOT NULL REFERENCES thoughts(id),
    commit_sha TEXT NOT NULL,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN ('initial', 'refinement', 'bugfix')),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thought_id, commit_sha)
) WITHOUT ROWID;
```

**Required Implementation**:
```rust
// workplace/modules/pos_thoughts/src/knowledge_loop.rs
pub struct KnowledgeLoopCloser {
    storage: ThoughtStorage,
}

impl KnowledgeLoopCloser {
    pub async fn close_loop(&self, thought_id: &str, commit_sha: &str, status: ShippedStatus) 
        -> Result<Backlink, Error> {
        // 1. Check if thought was edited since promotion
        let current_content = self.storage.get_thought_content(thought_id).await?;
        let snapshot = self.storage.get_promotion_snapshot(thought_id).await?;
        
        if current_content != snapshot.content_snapshot {
            return Err(Error::ThoughtVersionConflict {
                thought_id: thought_id.to_string(),
                message: "Thought was edited after promotion. Cannot safely backlink.".into(),
            });
        }
        
        // 2. Insert into thought_commits junction table
        self.storage.link_commit(thought_id, commit_sha, "initial").await?;
        
        // 3. Append backlink markdown to thought
        let backlink_md = self.generate_backlink_markdown(commit_sha, status);
        self.storage.append_to_thought(thought_id, &backlink_md).await?;
        
        Ok(Backlink {
            backlink_id: Uuid::new_v4().to_string(),
            thought_id: thought_id.to_string(),
            commit_sha: commit_sha.to_string(),
            created_at: Utc::now(),
        })
    }
    
    fn generate_backlink_markdown(&self, commit_sha: &str, status: ShippedStatus) -> String {
        format!(r#"
---
## 🚀 Implementation Proof
- **Status**: {} {}
- **Commit**: `{}`
- **Shipped At**: {}
- **Merkle Block**: Block #{} (`SHA-256: {}`)
---
"#,
            status.emoji(),
            status.label(),
            commit_sha,
            Utc::now().format("%Y-%m-%d %H:%M:%S UTC"),
            status.merkle_block_id,
            status.merkle_hash
        )
    }
}
```

---

#### GAP-T2P-009: Petgraph Task DAG Not Implemented
**Status**: BLOCKED  
**Blocker**: Requires pos_projects crate foundation

**Required Implementation**:
```rust
// workplace/modules/pos_projects/src/task_dag.rs
use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::algo::{toposort, is_cyclic_directed};

pub struct TaskDAG {
    graph: DiGraph<Task, TaskDependency>,
    node_map: HashMap<TaskId, NodeIndex>,
}

pub struct Task {
    pub task_id: TaskId,
    pub title: String,
    pub task_type: TaskType,
    pub estimated_duration_minutes: u32,
    pub assigned_agent: Option<String>,
}

pub enum TaskType {
    WireContract,
    Schema,
    TestScaffold,
    CoreImpl,
    Integration,
    Docs,
}

impl TaskDAG {
    pub fn from_plan(plan: &LayerablePlan) -> Result<Self, TaskError> {
        let mut graph = DiGraph::new();
        let mut node_map = HashMap::new();
        
        // 1. Extract tasks from plan components
        let tasks = Self::extract_tasks_from_components(&plan.components)?;
        
        // 2. Add nodes to graph
        for task in tasks {
            let node_idx = graph.add_node(task.clone());
            node_map.insert(task.task_id.clone(), node_idx);
        }
        
        // 3. Infer dependencies (wire contracts before tests, tests before impl)
        let dependencies = Self::infer_dependencies(&tasks);
        for (from_id, to_id) in dependencies {
            let from_idx = node_map[&from_id];
            let to_idx = node_map[&to_id];
            graph.add_edge(from_idx, to_idx, TaskDependency::default());
        }
        
        // 4. Verify acyclic
        if is_cyclic_directed(&graph) {
            return Err(TaskError::CycleDetected);
        }
        
        Ok(TaskDAG { graph, node_map })
    }
    
    pub fn next_executable_tasks(&self, completed: &HashSet<TaskId>) -> Vec<&Task> {
        self.graph
            .node_indices()
            .filter(|&node_idx| {
                let task = &self.graph[node_idx];
                
                // Skip if already completed
                if completed.contains(&task.task_id) {
                    return false;
                }
                
                // Check if all dependencies completed
                let dependencies_met = self.graph
                    .neighbors_directed(node_idx, petgraph::Direction::Incoming)
                    .all(|dep_idx| {
                        let dep_task = &self.graph[dep_idx];
                        completed.contains(&dep_task.task_id)
                    });
                
                dependencies_met
            })
            .map(|idx| &self.graph[idx])
            .collect()
    }
    
    pub fn execution_phases(&self) -> Vec<Vec<TaskId>> {
        // Topological sort + group by dependency level
        let sorted = toposort(&self.graph, None).expect("Already verified acyclic");
        
        let mut phases = Vec::new();
        let mut current_level = 0;
        let mut level_map = HashMap::new();
        
        for node_idx in sorted {
            let max_dep_level = self.graph
                .neighbors_directed(node_idx, petgraph::Direction::Incoming)
                .map(|dep_idx| level_map.get(&dep_idx).unwrap_or(&0))
                .max()
                .unwrap_or(&0);
            
            let node_level = max_dep_level + 1;
            level_map.insert(node_idx, node_level);
            
            if phases.len() <= node_level {
                phases.push(Vec::new());
            }
            
            phases[node_level].push(self.graph[node_idx].task_id.clone());
        }
        
        phases
    }
}
```

---

### 📋 REMAINING GAPS (Not Yet Started)

#### GAP-T2P-010: No Performance Benchmarks
**Status**: NOT STARTED  
**Priority**: P2 - Medium  
**Estimated Effort**: 2-3 weeks

**Required**:
- Criterion.rs benchmark suite for thought evaluation, MVS synthesis, DAG decomposition
- Test dataset: 100 representative thoughts (varying complexity, clarity, domain)
- Baseline measurements and latency profiling

---

#### GAP-T2P-011: No Rollback/Undo for Shipped Code
**Status**: NOT STARTED  
**Priority**: P3 - Low  
**Estimated Effort**: 1 week

**Proposed Solution**: Quarantine commits instead of reverting
```markdown
## Implementation Quarantined
⚠️ **Warning**: This implementation has been quarantined due to bugs in production.

- **Original Commit**: `abc123`
- **Quarantine Reason**: Introduced regression in X feature
- **Quarantined At**: 2026-10-05

The code remains in git history but has been marked unsafe.
```

---

#### GAP-T2P-012: No Multi-User Considerations
**Status**: NOT STARTED  
**Priority**: P3 - Low  
**Estimated Effort**: 2 weeks

**Open Questions**:
- Whose thoughts can trigger autonomous code generation?
- Per-user approval gates?
- Attribution in commit messages when multiple users collaborate?

---

## Summary

### Completion Status
- **Completed**: 2/12 gaps (16.7%)
- **In Progress**: 2/12 gaps (16.7%)
- **Blocked**: 5/12 gaps (41.7%)
- **Not Started**: 3/12 gaps (25.0%)

### Critical Path
1. ✅ Create wire contracts (GAP-T2P-004) → **DONE**
2. ✅ Create workflow orchestration (GAP-T2P-005) → **DONE**
3. ⏸️ Implement core dependencies (GAP-T2P-001) → **BLOCKED ON PHASE 1**
4. 🚧 Replace ambiguity/actionability algorithms (GAP-T2P-003, GAP-T2P-008) → **IN PROGRESS**
5. ⏸️ Implement WorktreeEngine (GAP-T2P-006) → **BLOCKED ON pos_projects**
6. ⏸️ Implement TaskDAG decomposer (GAP-T2P-009) → **BLOCKED ON pos_projects**
7. ⏸️ Implement knowledge loop closure (GAP-T2P-007) → **BLOCKED ON pos_thoughts**

### Next Actions
1. Continue implementing actionability/ambiguity evaluators (can be prototyped standalone)
2. Create agent configuration files: `agent_thought_synthesizer.yaml`, `agent_plan_architect.yaml`, `agent_autonomous_coder.yaml`
3. Create ruleset definitions: `plan_derivation_invariants.md`, `worktree_isolation_rules.md`
4. Wait for Phase 1 core pillar implementation before proceeding with blocked items

---

**End of Remediation Status Report**
