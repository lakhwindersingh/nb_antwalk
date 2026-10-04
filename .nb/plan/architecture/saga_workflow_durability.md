---
gap_id: "GAP-005"
name: "Persistent Workflow Durability via Saga Pattern"
priority: "P1"
status: "specification"
created: "2026-10-04"
---

# Saga Pattern for Long-Running Workflow Durability

## Problem Statement

Personal OS background workflows (email sync, file indexing, embedding generation) can run for **minutes to hours** and are vulnerable to:

1. **Process Crashes**: Application restart loses in-progress workflow state
2. **System Reboots**: macOS updates, power loss interrupt multi-step operations
3. **Network Failures**: Transient errors during IMAP sync or API calls
4. **Partial Completion**: Some steps succeed, others fail → inconsistent state
5. **No Retry Logic**: Failed workflows require manual user intervention

**Current Architecture Weakness**:
```yaml
# .nb/agentic/custom/workflows/wf_email_sync.yaml
steps:
  - tool: imap_fetch_emails        # Step 1: Fetch emails
    output: raw_emails
  - tool: extract_contacts          # Step 2: Extract contacts  
    output: contacts
  - tool: generate_embeddings       # Step 3: Embed content
    output: embeddings
  - tool: update_database           # Step 4: Store results
```

**Failure Scenario**:
- Step 1-2 complete successfully → 50 new contacts extracted
- Step 3 crashes during embedding generation (OOM, model load failure)
- Application restarts → **workflow state lost**
- Re-run attempts to fetch same emails again (duplicate processing)
- Extracted contacts orphaned, no embeddings generated
- Manual database cleanup required

**Impact**:
- Data inconsistency: Partial writes across multiple tables
- Wasted compute: Re-processing already-completed steps
- User confusion: "Why did my email sync fail halfway?"
- No visibility into workflow progress or failure reasons

---

## Solution Architecture: Saga Pattern with Compensating Transactions

Implement **persistent workflow orchestration** with durable state tracking, automatic retries, and compensation logic for rollback.

### Saga Pattern Overview

A **saga** is a sequence of local transactions where each transaction updates the database and publishes an event triggering the next step. If a step fails, **compensating transactions** undo the changes of preceding steps.

**Two Saga Variants**:
1. **Choreography**: Each service publishes events, next service listens (decentralized)
2. **Orchestration**: Central coordinator directs workflow execution (centralized)

**Personal OS Implementation**: **Orchestration-based saga** with `WorkflowOrchestrator` as central coordinator.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                   Workflow Definition (.yaml)                 │
│  steps:                                                       │
│    - tool: fetch_emails (compensate: mark_unprocessed)       │
│    - tool: extract_contacts (compensate: delete_contacts)    │
│    - tool: generate_embeddings (compensate: delete_embeddings)│
│    - tool: update_database (compensate: rollback_transaction)│
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              WorkflowOrchestrator (pos_workflows)             │
│                                                                │
│  ┌────────────────────────────────────────┐                  │
│  │  Workflow Execution State (SQLite)     │                  │
│  │  - workflow_id: uuid                   │                  │
│  │  - current_step: 2                     │                  │
│  │  - status: in_progress                 │                  │
│  │  - step_outputs: {fetch: [email_ids]}  │                  │
│  │  - retry_count: 0                      │                  │
│  └────────────────────────────────────────┘                  │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────┐                  │
│  │  Step Executor (Run/Retry/Compensate)  │                  │
│  │  - Execute step tool                   │                  │
│  │  - Save output to state                │                  │
│  │  - Mark step complete                  │                  │
│  │  - Trigger next step                   │                  │
│  └────────────────────────────────────────┘                  │
│                     │                                         │
│                     ▼                                         │
│  ┌────────────────────────────────────────┐                  │
│  │  Failure Handler (Retry/Compensate)    │                  │
│  │  - Check retry policy                  │                  │
│  │  - Execute compensating transactions   │                  │
│  │  - Restore consistent state            │                  │
│  └────────────────────────────────────────┘                  │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│          SQLite Database (Durable Workflow State)             │
│  - workflow_executions (main state)                           │
│  - workflow_step_log (step-by-step audit trail)               │
│  - compensating_transaction_log (rollback history)            │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Specification

### 1. SQLite Schema for Workflow State

```sql
-- Workflow execution state (durable across restarts)
CREATE TABLE IF NOT EXISTS workflow_executions (
    workflow_id TEXT PRIMARY KEY,
    workflow_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'compensating', 'compensated')),
    current_step_index INTEGER NOT NULL DEFAULT 0,
    total_steps INTEGER NOT NULL,
    input_params TEXT NOT NULL,  -- JSON
    step_outputs TEXT NOT NULL DEFAULT '{}',  -- JSON: {"step_1": {...}, "step_2": {...}}
    retry_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    error_message TEXT
);
CREATE INDEX idx_workflow_status ON workflow_executions(status);
CREATE INDEX idx_workflow_updated ON workflow_executions(updated_at);

-- Step-by-step audit trail
CREATE TABLE IF NOT EXISTS workflow_step_log (
    log_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflow_executions(workflow_id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    step_name TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'compensated')),
    input_params TEXT NOT NULL,  -- JSON
    output_result TEXT,  -- JSON
    error_message TEXT,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    duration_ms INTEGER
);
CREATE INDEX idx_step_log_workflow ON workflow_step_log(workflow_id, step_index);

-- Compensating transaction history
CREATE TABLE IF NOT EXISTS compensating_transaction_log (
    txn_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflow_executions(workflow_id) ON DELETE CASCADE,
    step_index INTEGER NOT NULL,
    compensating_tool TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    input_params TEXT NOT NULL,  -- JSON
    output_result TEXT,
    executed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_compensating_workflow ON compensating_transaction_log(workflow_id);
```

### 2. Workflow Definition with Compensation

```yaml
# .nb/agentic/custom/workflows/wf_email_sync_saga.yaml

name: "email_sync_saga"
description: "Durable email synchronization with compensation"
trigger: "schedule:0 */15 * * *"  # Every 15 minutes

saga_config:
  max_retries: 3
  retry_backoff: exponential  # 1s, 2s, 4s, 8s
  compensation_strategy: backward  # Rollback in reverse order

steps:
  - name: "fetch_emails"
    tool: "imap_fetch_unread_emails"
    timeout: 60s
    retry_policy:
      max_attempts: 3
      backoff: exponential
    compensation:
      tool: "mark_emails_unprocessed"
      input:
        email_ids: "{{output.email_ids}}"
    output_schema:
      email_ids: list[str]
      raw_emails: list[dict]

  - name: "extract_contacts"
    tool: "extract_contacts_from_emails"
    input:
      emails: "{{steps.fetch_emails.output.raw_emails}}"
    timeout: 120s
    compensation:
      tool: "delete_contacts_by_extraction_id"
      input:
        extraction_id: "{{workflow_id}}"
    output_schema:
      contact_ids: list[str]

  - name: "generate_embeddings"
    tool: "batch_embed_emails"
    input:
      email_ids: "{{steps.fetch_emails.output.email_ids}}"
    timeout: 300s
    compensation:
      tool: "delete_embeddings_by_workflow"
      input:
        workflow_id: "{{workflow_id}}"
    output_schema:
      embedding_ids: list[str]

  - name: "update_search_index"
    tool: "rebuild_email_search_index"
    timeout: 60s
    compensation:
      tool: "remove_from_search_index"
      input:
        email_ids: "{{steps.fetch_emails.output.email_ids}}"

  - name: "mark_complete"
    tool: "mark_emails_synced"
    input:
      email_ids: "{{steps.fetch_emails.output.email_ids}}"
    # No compensation needed (final step)
```

### 3. Workflow Orchestrator Core

```rust
// workplace/modules/pos_workflows/src/saga_orchestrator.rs

use sqlx::{SqlitePool, Transaction, Sqlite};
use serde_json::Value;
use tokio::time::{sleep, Duration};

pub struct SagaOrchestrator {
    pool: SqlitePool,
    tool_registry: Arc<ToolRegistry>,
    write_coordinator: Arc<WriteCoordinator>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorkflowExecution {
    pub workflow_id: String,
    pub workflow_name: String,
    pub status: WorkflowStatus,
    pub current_step_index: i32,
    pub total_steps: i32,
    pub input_params: Value,
    pub step_outputs: HashMap<String, Value>,
    pub retry_count: i32,
    pub max_retries: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum WorkflowStatus {
    Pending,
    InProgress,
    Completed,
    Failed,
    Compensating,
    Compensated,
}

impl SagaOrchestrator {
    pub async fn start_workflow(
        &self,
        definition: WorkflowDefinition,
        input_params: Value,
    ) -> Result<String, WorkflowError> {
        let workflow_id = ulid::Ulid::new().to_string();
        
        // Create workflow execution record
        sqlx::query!(
            "INSERT INTO workflow_executions 
             (workflow_id, workflow_name, status, total_steps, input_params, max_retries)
             VALUES (?, ?, ?, ?, ?, ?)",
            workflow_id,
            definition.name,
            "in_progress",
            definition.steps.len() as i32,
            serde_json::to_string(&input_params)?,
            definition.saga_config.max_retries
        )
        .execute(&self.pool)
        .await?;
        
        info!("Started workflow {} ({})", definition.name, workflow_id);
        
        // Execute workflow asynchronously
        let orchestrator = self.clone();
        tokio::spawn(async move {
            if let Err(e) = orchestrator.execute_workflow(workflow_id.clone(), definition).await {
                error!("Workflow  failed: {}", workflow_id, e);
                orchestrator.handle_workflow_failure(workflow_id, e).await;
            }
        });
        
        Ok(workflow_id)
    }
    
    async fn execute_workflow(
        &self,
        workflow_id: String,
        definition: WorkflowDefinition,
    ) -> Result<(), WorkflowError> {
        // Load workflow state (supports resume after restart)
        let mut execution = self.load_execution_state(&workflow_id).await?;
        
        // Execute remaining steps
        while (execution.current_step_index as usize) < definition.steps.len() {
            let step_index = execution.current_step_index as usize;
            let step = &definition.steps[step_index];
            
            info!("Executing step {}: {}", step_index, step.name);
            
            // Execute step with retry logic
            let result = self.execute_step_with_retry(
                &workflow_id,
                &mut execution,
                step,
            ).await;
            
            match result {
                Ok(output) => {
                    // Save step output
                    execution.step_outputs.insert(step.name.clone(), output);
                    execution.current_step_index += 1;
                    
                    // Persist state
                    self.save_execution_state(&execution).await?;
                }
                Err(e) => {
                    error!("Step {} failed: {}", step.name, e);
                    
                    // Trigger compensation
                    self.compensate_workflow(&execution, &definition, step_index).await?;
                    
                    return Err(WorkflowError::StepFailed(step.name.clone(), e.to_string()));
                }
            }
        }
        
        // Mark workflow complete
        self.mark_workflow_complete(&workflow_id).await?;
        
        info!("Workflow {} completed successfully", workflow_id);
        Ok(())
    }
    
    async fn execute_step_with_retry(
        &self,
        workflow_id: &str,
        execution: &mut WorkflowExecution,
        step: &WorkflowStep,
    ) -> Result<Value, WorkflowError> {
        let mut retry_count = 0;
        let max_retries = step.retry_policy.as_ref()
            .map(|p| p.max_attempts)
            .unwrap_or(1);
        
        loop {
            // Log step start
            let log_id = self.log_step_start(workflow_id, step).await?;
            
            let start_time = std::time::Instant::now();
            
            // Execute tool
            let result = tokio::time::timeout(
                step.timeout.unwrap_or(Duration::from_secs(300)),
                self.tool_registry.execute_tool(
                    &step.tool,
                    &self.resolve_input_params(step, execution)?,
                ),
            )
            .await;
            
            let duration_ms = start_time.elapsed().as_millis() as i64;
            
            match result {
                Ok(Ok(output)) => {
                    // Log step success
                    self.log_step_complete(&log_id, &output, duration_ms).await?;
                    return Ok(output);
                }
                Ok(Err(e)) | Err(_) => {
                    retry_count += 1;
                    
                    if retry_count >= max_retries {
                        // Log step failure
                        self.log_step_failed(&log_id, &e.to_string(), duration_ms).await?;
                        return Err(WorkflowError::ToolExecutionFailed(step.tool.clone(), e.to_string()));
                    }
                    
                    // Exponential backoff
                    let backoff_ms = step.retry_policy.as_ref()
                        .and_then(|p| match p.backoff {
                            BackoffStrategy::Exponential => Some(2_u64.pow(retry_count - 1) * 1000),
                            BackoffStrategy::Linear => Some(retry_count as u64 * 1000),
                            BackoffStrategy::Fixed(ms) => Some(ms),
                        })
                        .unwrap_or(1000);
                    
                    warn!("Step {} failed (attempt {}/{}), retrying in {}ms", 
                        step.name, retry_count, max_retries, backoff_ms);
                    
                    sleep(Duration::from_millis(backoff_ms)).await;
                }
            }
        }
    }
    
    async fn compensate_workflow(
        &self,
        execution: &WorkflowExecution,
        definition: &WorkflowDefinition,
        failed_step_index: usize,
    ) -> Result<(), WorkflowError> {
        info!("Starting compensation for workflow {}", execution.workflow_id);
        
        // Mark workflow as compensating
        self.update_workflow_status(&execution.workflow_id, WorkflowStatus::Compensating).await?;
        
        // Execute compensating transactions in reverse order
        for step_index in (0..failed_step_index).rev() {
            let step = &definition.steps[step_index];
            
            if let Some(compensation) = &step.compensation {
                info!("Compensating step {}: {}", step_index, step.name);
                
                let txn_id = ulid::Ulid::new().to_string();
                
                // Resolve compensation input from step output
                let compensation_input = self.resolve_compensation_input(
                    compensation,
                    execution,
                    step,
                )?;
                
                // Execute compensating tool
                let result = self.tool_registry.execute_tool(
                    &compensation.tool,
                    &compensation_input,
                ).await;
                
                // Log compensation result
                self.log_compensation(
                    &txn_id,
                    &execution.workflow_id,
                    step_index as i32,
                    &compensation.tool,
                    &compensation_input,
                    &result,
                ).await?;
                
                if let Err(e) = result {
                    error!("Compensation failed for step {}: {}", step.name, e);
                    // Continue with other compensations (best effort)
                }
            }
        }
        
        // Mark workflow as compensated
        self.update_workflow_status(&execution.workflow_id, WorkflowStatus::Compensated).await?;
        
        info!("Compensation complete for workflow {}", execution.workflow_id);
        Ok(())
    }
    
    async fn load_execution_state(&self, workflow_id: &str) -> Result<WorkflowExecution, WorkflowError> {
        let row = sqlx::query!(
            "SELECT workflow_name, status, current_step_index, total_steps, 
                    input_params, step_outputs, retry_count, max_retries
             FROM workflow_executions
             WHERE workflow_id = ?",
            workflow_id
        )
        .fetch_one(&self.pool)
        .await?;
        
        Ok(WorkflowExecution {
            workflow_id: workflow_id.to_string(),
            workflow_name: row.workflow_name,
            status: serde_json::from_str(&row.status)?,
            current_step_index: row.current_step_index,
            total_steps: row.total_steps,
            input_params: serde_json::from_str(&row.input_params)?,
            step_outputs: serde_json::from_str(&row.step_outputs)?,
            retry_count: row.retry_count,
            max_retries: row.max_retries,
        })
    }
    
    async fn save_execution_state(&self, execution: &WorkflowExecution) -> Result<(), WorkflowError> {
        sqlx::query!(
            "UPDATE workflow_executions
             SET current_step_index = ?, step_outputs = ?, retry_count = ?, updated_at = CURRENT_TIMESTAMP
             WHERE workflow_id = ?",
            execution.current_step_index,
            serde_json::to_string(&execution.step_outputs)?,
            execution.retry_count,
            execution.workflow_id
        )
        .execute(&self.pool)
        .await?;
        
        Ok(())
    }
    
    fn resolve_input_params(
        &self,
        step: &WorkflowStep,
        execution: &WorkflowExecution,
    ) -> Result<Value, WorkflowError> {
        // Replace template variables like "{{steps.fetch_emails.output.email_ids}}"
        let input_str = serde_json::to_string(&step.input)?;
        let resolved = self.replace_template_vars(&input_str, execution)?;
        Ok(serde_json::from_str(&resolved)?)
    }
    
    fn replace_template_vars(
        &self,
        template: &str,
        execution: &WorkflowExecution,
    ) -> Result<String, WorkflowError> {
        let mut result = template.to_string();
        
        // Replace {{workflow_id}}
        result = result.replace("{{workflow_id}}", &execution.workflow_id);
        
        // Replace {{steps.<step_name>.output.<field>}}
        let re = regex::Regex::new(r"\{\{steps\.([^.]+)\.output\.([^}]+)\}\}").unwrap();
        
        for capture in re.captures_iter(template) {
            let step_name = &capture[1];
            let field_name = &capture[2];
            
            if let Some(step_output) = execution.step_outputs.get(step_name) {
                if let Some(field_value) = step_output.get(field_name) {
                    result = result.replace(
                        &capture[0],
                        &serde_json::to_string(field_value)?,
                    );
                }
            }
        }
        
        Ok(result)
    }
}
```

### 4. Resume on Restart

```rust
impl SagaOrchestrator {
    /// Resume in-progress workflows after application restart
    pub async fn resume_interrupted_workflows(&self) -> Result<Vec<String>, WorkflowError> {
        let rows = sqlx::query!(
            "SELECT workflow_id, workflow_name
             FROM workflow_executions
             WHERE status IN ('in_progress', 'compensating')
             ORDER BY updated_at ASC"
        )
        .fetch_all(&self.pool)
        .await?;
        
        let mut resumed = Vec::new();
        
        for row in rows {
            info!("Resuming workflow {} ({})", row.workflow_name, row.workflow_id);
            
            // Load workflow definition from disk
            let definition = WorkflowDefinition::load(&row.workflow_name)?;
            
            // Continue execution from current step
            let orchestrator = self.clone();
            let workflow_id = row.workflow_id.clone();
            
            tokio::spawn(async move {
                if let Err(e) = orchestrator.execute_workflow(workflow_id.clone(), definition).await {
                    error!("Resumed workflow {} failed: {}", workflow_id, e);
                }
            });
            
            resumed.push(row.workflow_id);
        }
        
        Ok(resumed)
    }
}
```

### 5. CLI Workflow Management

```bash
# Start workflow manually
pos workflow run email_sync_saga

# Check workflow status
pos workflow status <workflow_id>

# List active workflows
pos workflow list --status in_progress

# Resume interrupted workflows after restart
pos workflow resume-all

# View workflow step log
pos workflow logs <workflow_id>

# Cancel running workflow with compensation
pos workflow cancel <workflow_id> --compensate
```

---

## Benefits

1. **Durability**: Workflow state survives crashes, reboots, network failures
2. **Automatic Recovery**: Resume from last completed step after restart
3. **Data Consistency**: Compensating transactions restore consistent state on failure
4. **Retry Logic**: Exponential backoff handles transient errors
5. **Auditability**: Complete step-by-step log for debugging
6. **Idempotency**: Safe to re-run workflows without duplicating side effects

---

## Performance Targets

| Metric | Target | Max |
|--------|--------|-----|
| Workflow state persist (per step) | 5ms | 20ms |
| Resume time after restart | 500ms | 2s |
| Compensation execution (per step) | 100ms | 500ms |
| Workflow overhead (vs. direct execution) | <5% | <15% |

---

## Migration Strategy

### Phase 1: Infrastructure (Week 1)
- Implement `SagaOrchestrator` core with state persistence
- Add workflow execution tables to SQLite schema
- Create `WorkflowDefinition` parser for YAML with compensation

### Phase 2: Integration (Week 2)
- Migrate `wf_email_sync` to saga pattern
- Add retry policies and compensating transactions
- Test failure scenarios (crash, network timeout)

### Phase 3: Rollout (Week 3)
- Migrate remaining workflows (`wf_file_indexing`, `wf_embedding_migration`)
- Add CLI workflow management commands
- Implement resume-on-restart in application startup

### Phase 4: Monitoring (Week 4)
- Add workflow execution metrics (duration, retry count, failure rate)
- Create workflow status dashboard
- Performance benchmarking

---

## Related Gaps

- **GAP-002** (Write Batching): Workflow state updates use `WriteCoordinator`
- **GAP-003** (Embedding Versioning): `wf_embedding_migration` uses saga pattern
- **GAP-001** (CRDT Sync): `wf_background_sync` compensation reverts CRDT updates

---

**Status**: ✅ Specification Complete - Ready for Implementation  
**Next Action**: Implement `SagaOrchestrator` in `workplace/modules/pos_workflows/src/saga_orchestrator.rs`
