# Meta-Orchestrator: Autonomous Request Router & Processor Dispatcher

## Overview

The **Meta-Orchestrator** is the top-level routing and delegation layer that sits above all domain-specific processing pipelines. It autonomously classifies incoming requests, selects appropriate processors, dynamically instantiates specialized agents/workflows, and manages result aggregation.

### Core Responsibility

Transform any user request — whether it's generating a software project, analyzing financial reports, reconciling databases, or conducting heavy computational analysis — into a routed execution plan that delegates to specialized processors.

### Key Design Principles

1. **Processor-Agnostic**: The meta-orchestrator doesn't implement domain logic; it routes to processors that do
2. **Dynamic Processor Registry**: New processors can be registered without modifying the core router
3. **Intent-Based Routing**: Uses LLM-based semantic classification to determine request intent
4. **Autonomous Delegation**: Creates and manages specialized agent teams and workflows without human intervention
5. **Unified Result Aggregation**: Collects and synthesizes results from multiple processors

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Meta-Orchestrator Core                      │
│                                                                 │
│  ┌──────────────────┐     ┌────────────────────────────────┐  │
│  │ Request Intake   │────▶│ Intent Classifier (LLM-based)  │  │
│  └──────────────────┘     └────────────────────────────────┘  │
│                                       │                         │
│                                       ▼                         │
│                          ┌─────────────────────┐               │
│                          │ Processor Registry  │               │
│                          │   - thought_to_      │               │
│                          │     project          │               │
│                          │   - financial_       │               │
│                          │     analysis         │               │
│                          │   - database_        │               │
│                          │     reconciliation   │               │
│                          │   - heavy_analysis   │               │
│                          │   - custom_*         │               │
│                          └─────────────────────┘               │
│                                       │                         │
│                                       ▼                         │
│  ┌────────────────────────────────────────────────────────┐   │
│  │      Dynamic Workflow/Agent Instantiation Engine       │   │
│  │  - Provisions ephemeral worktrees                      │   │
│  │  - Creates specialized agent teams                     │   │
│  │  - Configures processor-specific contexts              │   │
│  └────────────────────────────────────────────────────────┘   │
│                                       │                         │
│                                       ▼                         │
│  ┌────────────────────────────────────────────────────────┐   │
│  │           Result Aggregator & Synthesizer              │   │
│  │  - Collects processor outputs                          │   │
│  │  - Synthesizes cross-processor insights                │   │
│  │  - Generates unified reports                           │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   User Presentation   │
                    │   - Reports           │
                    │   - Artifacts         │
                    │   - Action Items      │
                    └───────────────────────┘
```

---

## Request Classification

The meta-orchestrator uses LLM-based semantic analysis to classify requests into categories:

### Classification Dimensions

1. **Primary Intent**
   - `project_generation`: Convert thought/idea into executable software project
   - `data_analysis`: Analyze structured or unstructured data
   - `reconciliation`: Compare and align data from multiple sources
   - `computation`: Perform heavy computational work (simulations, modeling)
   - `information_extraction`: Extract structured data from unstructured sources
   - `synthesis`: Combine multiple inputs into unified output

2. **Complexity Level**
   - `simple`: Single-step, single-processor task
   - `moderate`: Multi-step within single processor
   - `complex`: Multi-processor coordination required
   - `exploratory`: Requires iterative refinement

3. **Urgency**
   - `immediate`: Return results synchronously
   - `background`: Queue for async execution
   - `scheduled`: Defer to specific time

4. **Data Sensitivity**
   - `public`: No confidential data
   - `internal`: Company/personal data
   - `confidential`: Requires enhanced security

---

## Processor Registry Schema

Each processor is registered with the following specification:

```yaml
processor_id: thought_to_project
processor_name: Thought-to-Project Pipeline
version: 1.0.0
processor_type: domain_specific
supported_intents:
  - project_generation
  - specification_synthesis
complexity_levels: [simple, moderate, complex]
entry_point: .nb/plan/extensions/thought_to_project/concise.md
agent_requirements:
  - agent_thought_synthesizer
  - agent_plan_architect
  - agent_autonomous_coder
workflow_requirements:
  - wf_thought_to_plan
  - wf_plan_to_cicd
resource_requirements:
  ephemeral_worktrees: true
  git_operations: true
  llm_calls: high_frequency
input_schema:
  type: object
  required: [thought_content, domain_hint]
  properties:
    thought_content: { type: string }
    domain_hint: { type: string }
output_schema:
  type: object
  required: [status, plan_path, artifacts]
  properties:
    status: { type: string, enum: [success, partial, failed] }
    plan_path: { type: string }
    artifacts: { type: array }
estimated_duration_seconds: 300
```

---

## Meta-Orchestrator Wire Contract

```yaml
schema_version: 1.0.0
domain: meta_orchestration
service_endpoint: /api/v1/orchestrate
methods:
  - name: classify_and_route
    description: Classify request intent and route to appropriate processor(s)
    input_schema:
      type: object
      required: [request_text, context]
      properties:
        request_text: { type: string }
        context:
          type: object
          properties:
            user_id: { type: string }
            session_id: { type: string }
            urgency: { type: string, enum: [immediate, background, scheduled] }
            available_context: { type: array, items: { type: string } }
    output_schema:
      type: object
      required: [classification, routing_plan, execution_id]
      properties:
        classification:
          type: object
          properties:
            primary_intent: { type: string }
            complexity: { type: string }
            confidence: { type: number }
        routing_plan:
          type: array
          items:
            type: object
            properties:
              processor_id: { type: string }
              execution_order: { type: integer }
              dependencies: { type: array, items: { type: string } }
        execution_id: { type: string }

  - name: execute_routed_request
    description: Execute the classified request through routed processors
    input_schema:
      type: object
      required: [execution_id, routing_plan, request_payload]
      properties:
        execution_id: { type: string }
        routing_plan: { type: object }
        request_payload: { type: object }
    output_schema:
      type: object
      required: [status, processor_results, aggregated_output]
      properties:
        status: { type: string, enum: [completed, partial, failed, queued] }
        processor_results:
          type: array
          items:
            type: object
            properties:
              processor_id: { type: string }
              status: { type: string }
              output: { type: object }
              duration_seconds: { type: number }
        aggregated_output: { type: object }

  - name: register_processor
    description: Register a new processor with the meta-orchestrator
    input_schema:
      type: object
      required: [processor_spec]
      properties:
        processor_spec: { type: object }
    output_schema:
      type: object
      required: [registration_status, processor_id]
      properties:
        registration_status: { type: string, enum: [registered, rejected] }
        processor_id: { type: string }
        validation_errors: { type: array }
```

---

## Example Use Cases

### Use Case 1: Project Generation (Existing)
**Request**: "Implement LRU cache with 1000 entry capacity..."
- **Classification**: `project_generation` / `moderate` / `immediate`
- **Routing**: `thought_to_project` processor
- **Execution**: Delegates to agent_thought_synthesizer → agent_plan_architect → agent_autonomous_coder
- **Output**: Layerable domain plan + ephemeral worktree + CI/CD execution

### Use Case 2: Financial Report Analysis (New)
**Request**: "Analyze Q3 revenue report and compare with Q2, highlighting variances >10%"
- **Classification**: `data_analysis` / `moderate` / `immediate`
- **Routing**: `financial_analysis` processor
- **Execution**: Creates agent_financial_analyzer + agent_variance_detector
- **Output**: Structured variance report with visualizations

### Use Case 3: Database Reconciliation (New)
**Request**: "Reconcile customer records between PostgreSQL prod and Salesforce, flag duplicates"
- **Classification**: `reconciliation` / `complex` / `background`
- **Routing**: `database_reconciliation` processor
- **Execution**: Creates agent_db_connector + agent_reconciliation_engine
- **Output**: Reconciliation report + duplicate candidates + merge suggestions

### Use Case 4: Heavy Computational Analysis (New)
**Request**: "Run Monte Carlo simulation with 10M iterations on portfolio risk model"
- **Classification**: `computation` / `complex` / `background`
- **Routing**: `heavy_analysis` processor
- **Execution**: Provisions compute resources + creates agent_simulation_runner
- **Output**: Statistical distribution + risk metrics + confidence intervals

---

## Integration with Existing Infrastructure

### Relationship to thought_to_project
- `thought_to_project` becomes **one processor** among many
- Meta-orchestrator routes project-generation requests to it
- `thought_to_project` continues to use existing agents and workflows unchanged

### Relationship to Parent Master Plan
- Meta-orchestrator follows same tier mapping and model tiering policy
- Inherits all safety invariants and verification protocols
- Extends quad-space structure with meta-orchestration layer

### Relationship to Autonomous CI/CD Triad
- Meta-orchestrator delegates to CI/CD triad when processors require code execution
- Maintains same Merkle sealing and cryptographic traceability
- Extends triad to support non-code artifacts (reports, analyses, reconciliations)

---

## Implementation Phases

### Phase 1: Core Router Infrastructure (Current)
- [ ] Intent classifier implementation (LLM-based)
- [ ] Processor registry system
- [ ] Basic routing logic
- [ ] Integration with thought_to_project as first processor

### Phase 2: Dynamic Agent/Workflow Instantiation
- [ ] Template-based agent generation
- [ ] Workflow orchestration engine
- [ ] Resource provisioning (worktrees, compute)
- [ ] Result aggregation framework

### Phase 3: Additional Processors
- [ ] Financial analysis processor
- [ ] Database reconciliation processor
- [ ] Heavy computation processor
- [ ] Custom processor plugin system

### Phase 4: Advanced Features
- [ ] Multi-processor coordination
- [ ] Iterative refinement loops
- [ ] Cross-processor knowledge sharing
- [ ] Autonomous processor discovery and registration

---

## Next Steps

1. **Design intent classification system** (LLM prompt + structured output)
2. **Create processor registry schema and storage**
3. **Implement basic routing engine**
4. **Retrofit thought_to_project as registered processor**
5. **Build result aggregation framework**
6. **Create templates for new processor types**
