# Meta-Orchestrator Implementation Roadmap

## Overview

This document outlines the implementation phases for the meta-orchestrator system, which provides autonomous request routing and multi-processor coordination for Personal OS.

---

## Phase 1: Core Router Infrastructure (Weeks 1-2)

### Goals
- Establish basic intent classification system
- Create processor registry infrastructure
- Implement routing logic for single-processor requests
- Integrate thought_to_project as first registered processor

### Deliverables

#### 1.1 Intent Classification Module
**Location**: `workplace/modules/pos_orchestrator/src/classifier.rs`

```rust
pub struct IntentClassifier {
    llm_client: Box<dyn LLMClient>,
    classification_cache: Arc<RwLock<LruCache<String, Classification>>>,
}

pub struct Classification {
    pub primary_intent: Intent,
    pub secondary_intents: Vec<Intent>,
    pub complexity: ComplexityLevel,
    pub confidence: f64,
    pub extracted_entities: Vec<Entity>,
    pub resource_estimates: ResourceEstimates,
    pub warnings: Vec<Warning>,
}

pub enum Intent {
    ProjectGeneration,
    DataAnalysis,
    Reconciliation,
    Computation,
    InformationExtraction,
    Synthesis,
    Monitoring,
    Optimization,
}
```

**Implementation Tasks**:
- [ ] Create `pos_orchestrator` crate under `workplace/modules/`
- [ ] Implement `IntentClassifier` with LLM-based classification
- [ ] Add classification prompt template (see WIRE_CONTRACTS.yaml)
- [ ] Implement LRU cache for classification results (5 min TTL)
- [ ] Add entity extraction using existing `agent_entity_extractor.yaml`
- [ ] Write unit tests with mock LLM responses
- [ ] Write integration tests with real classification examples

**Dependencies**:
- Reuse `LLMClient` trait from `pos_thoughts`
- Use `lru` crate for caching
- Use `serde` for JSON schema validation

---

#### 1.2 Processor Registry
**Location**: `workplace/modules/pos_orchestrator/src/registry.rs`

```rust
pub struct ProcessorRegistry {
    processors: HashMap<ProcessorId, ProcessorSpec>,
    intent_index: HashMap<Intent, Vec<ProcessorId>>,
    registry_path: PathBuf,
}

pub struct ProcessorSpec {
    pub processor_id: String,
    pub processor_name: String,
    pub version: String,
    pub supported_intents: Vec<Intent>,
    pub complexity_levels: Vec<ComplexityLevel>,
    pub entry_point: PathBuf,
    pub agent_requirements: Vec<String>,
    pub workflow_requirements: Vec<String>,
    pub resource_requirements: ResourceRequirements,
    pub input_schema: JsonSchema,
    pub output_schema: JsonSchema,
    pub estimated_duration_seconds: u64,
    pub priority: u8,
    pub classification_hints: ClassificationHints,
}
```

**Implementation Tasks**:
- [ ] Implement YAML-based processor registry loader
- [ ] Create intent-to-processor index for fast lookups
- [ ] Implement processor validation (check agents/workflows exist)
- [ ] Add processor registration API
- [ ] Implement processor scoring algorithm (confidence × priority)
- [ ] Write tests for registry CRUD operations
- [ ] Create thought_to_project processor registration file

**Dependencies**:
- Use `serde_yaml` for registry parsing
- Use `jsonschema` for schema validation
- Integration with `.nb/agentic/custom/agents/` discovery

---

#### 1.3 Basic Routing Engine
**Location**: `workplace/modules/pos_orchestrator/src/router.rs`

```rust
pub struct Router {
    classifier: IntentClassifier,
    registry: ProcessorRegistry,
}

pub struct RoutingPlan {
    pub execution_id: Uuid,
    pub processors: Vec<ProcessorStep>,
    pub resource_allocation: ResourceAllocation,
    pub estimated_duration_seconds: u64,
}

pub struct ProcessorStep {
    pub processor_id: String,
    pub execution_order: u32,
    pub dependencies: Vec<String>,
    pub input_mapping: serde_json::Value,
    pub resource_allocation: ResourceAllocation,
    pub fallback_processor_id: Option<String>,
}
```

**Implementation Tasks**:
- [ ] Implement `classify_and_route` method
- [ ] Add processor selection logic (highest confidence + priority)
- [ ] Implement resource estimation
- [ ] Add routing plan serialization
- [ ] Handle low-confidence classification (emit to HITL)
- [ ] Write routing tests for common request types
- [ ] Integration test: route "implement LRU cache" to thought_to_project

**Dependencies**:
- `uuid` for execution ID generation
- Integration with `IntentClassifier` and `ProcessorRegistry`

---

#### 1.4 Integration with thought_to_project
**Location**: `.nb/plan/extensions/meta_orchestrator/processors/thought_to_project.yaml`

**Implementation Tasks**:
- [ ] Create thought_to_project processor registration (copy from PROCESSOR_REGISTRY_SCHEMA.yaml)
- [ ] Implement delegation to thought_to_project workflow
- [ ] Test end-to-end: request → classification → routing → thought_to_project execution
- [ ] Validate output artifacts match schema
- [ ] Add telemetry collection

---

### Testing & Validation

#### Test Cases
1. **Classification Accuracy**
   - 20+ diverse requests with ground-truth labels
   - Target: 85%+ classification accuracy

2. **Routing Correctness**
   - Route project generation requests to thought_to_project
   - Handle low-confidence classification correctly
   - Validate processor requirements before routing

3. **End-to-End Integration**
   - Submit "Implement Redis-backed session store" request
   - Verify: classification → routing → thought_to_project → MVS generation → code generation

---

## Phase 2: Dynamic Agent/Workflow Instantiation (Weeks 3-4)

### Goals
- Enable dynamic creation of specialized agent teams
- Implement workflow orchestration engine
- Add resource provisioning (ephemeral worktrees, compute)
- Build result aggregation framework

### Deliverables

#### 2.1 Agent Instantiation Engine
**Location**: `workplace/modules/pos_orchestrator/src/agent_factory.rs`

```rust
pub struct AgentFactory {
    agent_specs_path: PathBuf,
    active_agents: HashMap<AgentInstanceId, AgentInstance>,
}

pub struct AgentInstance {
    pub instance_id: Uuid,
    pub agent_id: String,
    pub config: AgentConfig,
    pub state: AgentState,
}
```

**Implementation Tasks**:
- [ ] Load agent specs from `.nb/agentic/custom/agents/`
- [ ] Implement agent instantiation with config overrides
- [ ] Add agent lifecycle management (start, stop, monitor)
- [ ] Implement agent pool for reuse
- [ ] Write tests for agent creation and cleanup

---

#### 2.2 Workflow Orchestration Engine
**Location**: `workplace/modules/pos_orchestrator/src/workflow_engine.rs`

```rust
pub struct WorkflowEngine {
    active_workflows: HashMap<ExecutionId, WorkflowExecution>,
}

pub struct WorkflowExecution {
    pub execution_id: Uuid,
    pub workflow_id: String,
    pub steps: Vec<WorkflowStep>,
    pub state: ExecutionState,
    pub progress: ExecutionProgress,
}
```

**Implementation Tasks**:
- [ ] Implement workflow step executor
- [ ] Add dependency resolution (DAG traversal)
- [ ] Implement parallel step execution
- [ ] Add progress tracking and telemetry
- [ ] Implement timeout and retry logic
- [ ] Write workflow execution tests

---

#### 2.3 Resource Provisioning
**Location**: `workplace/modules/pos_orchestrator/src/resources.rs`

```rust
pub struct ResourceProvisioner {
    worktree_manager: WorktreeManager,
    compute_allocator: ComputeAllocator,
}
```

**Implementation Tasks**:
- [ ] Integrate with `pos_projects` worktree management
- [ ] Implement resource quota enforcement
- [ ] Add resource cleanup on execution completion
- [ ] Write resource allocation tests

---

#### 2.4 Result Aggregation Framework
**Location**: `workplace/modules/pos_orchestrator/src/aggregator.rs`

```rust
pub struct ResultAggregator {
    llm_client: Box<dyn LLMClient>,
}

pub struct AggregatedOutput {
    pub summary: String,
    pub artifacts: Vec<Artifact>,
    pub actionable_items: Vec<ActionItem>,
    pub cross_processor_insights: Vec<Insight>,
}
```

**Implementation Tasks**:
- [ ] Collect processor outputs and artifacts
- [ ] Implement LLM-based insight synthesis
- [ ] Generate unified reports
- [ ] Extract actionable items
- [ ] Write aggregation tests

---

### Testing & Validation

#### Test Cases
1. **Agent Instantiation**
   - Create multiple agent instances from specs
   - Verify config overrides work correctly
   - Test agent cleanup

2. **Workflow Execution**
   - Execute multi-step workflow with dependencies
   - Test parallel step execution
   - Verify timeout handling

3. **Resource Management**
   - Provision and cleanup ephemeral worktrees
   - Enforce resource quotas
   - Handle resource exhaustion

---

## Phase 3: Additional Processors (Weeks 5-7)

### Goals
- Implement financial_analysis processor
- Implement database_reconciliation processor
- Implement heavy_analysis processor
- Create custom processor plugin system

### Deliverables

#### 3.1 Financial Analysis Processor
**Location**: `.nb/plan/extensions/financial_analysis/`

**Components**:
- [ ] `concise.md` - Layerable domain plan
- [ ] `agent_financial_analyzer.yaml` - Data ingestion and parsing
- [ ] `agent_variance_detector.yaml` - Variance calculation
- [ ] `agent_report_synthesizer.yaml` - Report generation
- [ ] `wf_financial_analysis.yaml` - End-to-end workflow

**Input**: Financial reports (CSV, XLSX, PDF)
**Output**: Variance report with visualizations and insights

---

#### 3.2 Database Reconciliation Processor
**Location**: `.nb/plan/extensions/database_reconciliation/`

**Components**:
- [ ] `concise.md` - Layerable domain plan
- [ ] `agent_db_connector.yaml` - Multi-source DB connection
- [ ] `agent_reconciliation_engine.yaml` - Record matching
- [ ] `agent_duplicate_detector.yaml` - Duplicate identification
- [ ] `wf_database_reconciliation.yaml` - End-to-end workflow

**Input**: Multiple database connection specs + reconciliation rules
**Output**: Reconciliation report with matched/unmatched/duplicate records

---

#### 3.3 Heavy Analysis Processor
**Location**: `.nb/plan/extensions/heavy_analysis/`

**Components**:
- [ ] `concise.md` - Layerable domain plan
- [ ] `agent_computation_orchestrator.yaml` - Compute provisioning
- [ ] `agent_simulation_runner.yaml` - Parallel execution
- [ ] `agent_result_synthesizer.yaml` - Statistical aggregation
- [ ] `wf_heavy_computation.yaml` - End-to-end workflow

**Input**: Computation type (Monte Carlo, optimization) + parameters
**Output**: Statistical results with confidence intervals

---

#### 3.4 Custom Processor Plugin System
**Location**: `workplace/modules/pos_orchestrator/src/plugins.rs`

**Implementation Tasks**:
- [ ] Define plugin interface
- [ ] Implement plugin discovery and loading
- [ ] Add plugin validation
- [ ] Write plugin SDK documentation
- [ ] Create example custom processor

---

### Testing & Validation

#### Test Cases
1. **Financial Analysis**
   - Analyze sample Q3 vs Q2 revenue report
   - Verify variance detection (>10% threshold)
   - Validate report generation

2. **Database Reconciliation**
   - Reconcile sample customer records from two mock databases
   - Verify duplicate detection
   - Test conflict resolution strategies

3. **Heavy Analysis**
   - Run sample Monte Carlo simulation (10K iterations)
   - Verify statistical output correctness
   - Test parallel execution efficiency

---

## Phase 4: Advanced Features (Weeks 8-10)

### Goals
- Multi-processor coordination
- Iterative refinement loops
- Cross-processor knowledge sharing
- Autonomous processor discovery

### Deliverables

#### 4.1 Multi-Processor Coordination
**Location**: `workplace/modules/pos_orchestrator/src/coordinator.rs`

**Implementation Tasks**:
- [ ] Implement inter-processor data contracts
- [ ] Add shared state management
- [ ] Implement processor dependency resolution
- [ ] Write multi-processor tests

---

#### 4.2 Iterative Refinement
**Location**: `workplace/modules/pos_orchestrator/src/refinement.rs`

**Implementation Tasks**:
- [ ] Detect incomplete results
- [ ] Implement feedback loop to classification
- [ ] Add automatic retry with refined input
- [ ] Write refinement tests

---

#### 4.3 Cross-Processor Knowledge Sharing
**Location**: `workplace/modules/pos_orchestrator/src/knowledge.rs`

**Implementation Tasks**:
- [ ] Create shared knowledge graph
- [ ] Implement entity linking across processors
- [ ] Add insight correlation
- [ ] Write knowledge sharing tests

---

#### 4.4 Autonomous Processor Discovery
**Location**: `workplace/modules/pos_orchestrator/src/discovery.rs`

**Implementation Tasks**:
- [ ] Implement filesystem-based processor discovery
- [ ] Add automatic registration
- [ ] Implement processor health checks
- [ ] Write discovery tests

---

### Testing & Validation

#### Test Cases
1. **Multi-Processor Coordination**
   - Request requiring both financial_analysis and database_reconciliation
   - Verify data contract enforcement
   - Test parallel vs sequential execution

2. **Iterative Refinement**
   - Submit ambiguous request
   - Verify refinement loop triggers
   - Test convergence to actionable result

3. **Knowledge Sharing**
   - Execute multiple processors
   - Verify entity linking
   - Test cross-processor insight generation

---

## Implementation Priorities

### P0 (Must Have for MVP)
- [x] Meta-orchestrator architecture design (this document)
- [ ] Intent classification module
- [ ] Processor registry
- [ ] Basic routing engine
- [ ] Integration with thought_to_project

### P1 (Core Functionality)
- [ ] Agent instantiation engine
- [ ] Workflow orchestration engine
- [ ] Resource provisioning
- [ ] Result aggregation

### P2 (Enhanced Capabilities)
- [ ] Financial analysis processor
- [ ] Database reconciliation processor
- [ ] Multi-processor coordination

### P3 (Advanced Features)
- [ ] Heavy analysis processor
- [ ] Custom processor plugin system
- [ ] Iterative refinement
- [ ] Autonomous processor discovery

---

## Success Metrics

### Classification Performance
- **Classification Accuracy**: >85% on test set
- **Classification Latency**: <500ms p95
- **Confidence Score Reliability**: Correlation with actual success >0.80

### Routing Performance
- **Routing Latency**: <1000ms p95
- **Processor Match Accuracy**: >90%
- **Resource Estimation Accuracy**: Within 2x actual usage

### End-to-End Performance
- **Orchestration Overhead**: <2000ms p95
- **Processor Success Rate**: >80%
- **User Satisfaction**: >4.0/5.0

---

## Risk Mitigation

### Risk 1: Low Classification Accuracy
**Mitigation**: 
- Extensive test set creation with diverse requests
- Iterative prompt engineering
- Fallback to rule-based classification

### Risk 2: Processor Compatibility Issues
**Mitigation**:
- Strict schema validation
- Comprehensive integration tests
- Version compatibility checking

### Risk 3: Resource Exhaustion
**Mitigation**:
- Resource quotas and limits
- Queueing for high-load scenarios
- Graceful degradation

### Risk 4: Long Implementation Timeline
**Mitigation**:
- Phased rollout (thought_to_project first)
- Placeholder processors for Phase 3
- Parallel development tracks

---

## Dependencies

### Internal Dependencies
- `pos_thoughts` (LLMClient trait, entity extraction)
- `pos_projects` (worktree management, task DAG)
- `pos_agents` (agent execution runtime)
- `.nb/core/autonomous_cicd.py` (CI/CD triad)

### External Dependencies
- LLM API (Claude Sonnet 5 / GPT-4o)
- JSON Schema validation library (`jsonschema`)
- Workflow orchestration (`petgraph` for DAG)
- Caching (`lru` crate)

---

## Next Steps

1. **Week 1**: Create `pos_orchestrator` crate structure
2. **Week 1**: Implement `IntentClassifier` with unit tests
3. **Week 1-2**: Implement `ProcessorRegistry` and basic `Router`
4. **Week 2**: Register thought_to_project and test end-to-end
5. **Week 3**: Begin Phase 2 (agent instantiation)

---

## Appendix: File Structure

```
.nb/plan/extensions/meta_orchestrator/
├── README.md                          # Architecture overview (DONE)
├── WIRE_CONTRACTS.yaml                # API contracts (DONE)
├── PROCESSOR_REGISTRY_SCHEMA.yaml     # Processor registration format (DONE)
├── IMPLEMENTATION_ROADMAP.md          # This file (DONE)
├── processors/
│   ├── thought_to_project.yaml        # TODO: Week 2
│   ├── financial_analysis.yaml        # TODO: Week 5
│   ├── database_reconciliation.yaml   # TODO: Week 6
│   └── heavy_analysis.yaml            # TODO: Week 7

.nb/agentic/custom/agents/
├── agent_meta_orchestrator.yaml       # Meta-orchestrator agent (DONE)

.nb/agentic/custom/workflows/
├── wf_orchestrate_request.yaml        # Main orchestration workflow (DONE)

workplace/modules/pos_orchestrator/
├── Cargo.toml                         # TODO: Week 1
├── src/
│   ├── lib.rs                         # TODO: Week 1
│   ├── classifier.rs                  # TODO: Week 1
│   ├── registry.rs                    # TODO: Week 1-2
│   ├── router.rs                      # TODO: Week 2
│   ├── agent_factory.rs               # TODO: Week 3
│   ├── workflow_engine.rs             # TODO: Week 3
│   ├── resources.rs                   # TODO: Week 4
│   ├── aggregator.rs                  # TODO: Week 4
│   ├── coordinator.rs                 # TODO: Week 8
│   ├── refinement.rs                  # TODO: Week 9
│   ├── knowledge.rs                   # TODO: Week 9
│   ├── discovery.rs                   # TODO: Week 10
│   └── plugins.rs                     # TODO: Week 7
├── tests/
│   ├── classification_tests.rs        # TODO: Week 1
│   ├── routing_tests.rs               # TODO: Week 2
│   └── integration_tests.rs           # TODO: Week 2
```
