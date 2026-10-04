# Plan Derivation Invariants

**Version**: 1.0.0  
**Status**: Foundation  
**Scope**: Thought-to-Project extension - plan compilation and validation

## Purpose

This document defines inviolable invariants that must hold during the transformation
of unstructured thoughts → MVS specifications → layerable domain plans. These
invariants ensure consistency, traceability, and correctness throughout the pipeline.

## Core Invariants

### INV-PD-01: Thought-MVS-Plan Chain of Custody

**Rule**: Every layerable plan must trace back to exactly one MVS specification,
which must trace back to exactly one thought (or manual MVS creation).

**Rationale**: Enables bidirectional knowledge loop closure. When code is shipped,
we must be able to trace back to the original thought that inspired it.

**Enforcement**:
```yaml
# Every MVS must include:
mvs_id: uuid (unique identifier)
thought_id: uuid | null (null only if manually created)

# Every plan must include:
plan_id: uuid (unique identifier)
mvs_source: path to MVS YAML file
originating_thought: uuid | null (extracted from MVS)
```

**Verification**:
- Before compiling plan, verify MVS file exists and contains valid `mvs_id`
- After plan generation, write metadata file: `.nb/plan/extensions/{domain}/.metadata.yaml`
- On thought query, retrieve all linked plans via `thought_id` → `mvs_id` → `plan_id`

**Violation Consequences**:
- Plan compilation fails with error: `E_BROKEN_CHAIN_OF_CUSTODY`
- Prevents orphaned plans that cannot be traced to requirements


### INV-PD-02: MVS Schema Compliance

**Rule**: Every MVS specification must validate against `plan_synthesis_contract.json`
before plan compilation proceeds.

**Rationale**: Ensures consistent structure for plan compilation. Invalid MVS leads
to unpredictable plan generation.

**Enforcement**:
```rust
pub fn validate_mvs(mvs_path: &Path) -> Result<MvsSpec, ValidationError> {
    let schema = JsonSchema::load("plan_synthesis_contract.json")?;
    let mvs_content = fs::read_to_string(mvs_path)?;
    let mvs: Value = serde_yaml::from_str(&mvs_content)?;
    
    schema.validate(&mvs)?;  // Fails if schema violations
    
    Ok(serde_yaml::from_value(mvs)?)
}
```

**Required Fields** (per schema):
- `mvs_id`, `domain`, `title`, `slug`
- `components` (minItems: 1)
- `constraints` (array, may be empty)
- `acceptance_criteria` (minItems: 3)

**Violation Consequences**:
- MVS synthesis fails, quarantined to `user/hitl/poisoned_mvs_specs/`
- Error message includes specific schema violations
- No plan generation attempted


### INV-PD-03: Component Completeness

**Rule**: Every component referenced in a plan must have:
1. A definition in the source MVS `components` array
2. A contract file generated (if component has interfaces)
3. All dependencies resolvable to other components or external crates

**Rationale**: Prevents partial/incomplete plans that cannot be implemented.

**Enforcement**:
```rust
pub fn verify_component_completeness(plan: &LayerablePlan, mvs: &MvsSpec) 
    -> Result<(), CompletenessError> {
    for component in &plan.components {
        // 1. Component exists in MVS
        let mvs_component = mvs.components.iter()
            .find(|c| c.name == component.name)
            .ok_or(CompletenessError::ComponentNotInMvs(component.name.clone()))?;
        
        // 2. Contract generated if needed
        if !mvs_component.interfaces.is_empty() {
            let contract_path = format!("workplace/contracts/{}.rs", component.name);
            if !Path::new(&contract_path).exists() {
                return Err(CompletenessError::MissingContract(component.name.clone()));
            }
        }
        
        // 3. Dependencies resolvable
        for dep in &mvs_component.dependencies {
            if !component_exists(dep, mvs) && !is_external_crate(dep) {
                return Err(CompletenessError::UnresolvedDependency {
                    component: component.name.clone(),
                    dependency: dep.clone(),
                });
            }
        }
    }
    
    Ok(())
}
```

**Violation Consequences**:
- Plan validation fails with `validation_status: invalid`
- Specific missing components/contracts listed in `validation_issues`
- Plan quarantined, not executable


### INV-PD-04: Task DAG Acyclicity

**Rule**: Decomposed task DAGs must be acyclic. No circular dependencies allowed.

**Rationale**: Cyclic task dependencies make execution ordering impossible.
Indicates architectural flaw in component design.

**Enforcement**:
```rust
use petgraph::algo::is_cyclic_directed;

pub fn validate_task_dag(dag: &TaskDAG) -> Result<(), DagError> {
    if is_cyclic_directed(&dag.graph) {
        // Find cycle for debugging
        let cycle = find_cycle(&dag.graph)?;
        return Err(DagError::CyclicDependency {
            cycle: cycle.iter().map(|n| dag.graph[*n].name.clone()).collect(),
        });
    }
    
    Ok(())
}
```

**Automatic Cycle Detection**:
- Run `petgraph::is_cyclic_directed()` after DAG construction
- If cycle detected, extract cycle path and report to user
- Do NOT attempt to auto-fix (requires architectural decision)

**Violation Consequences**:
- DAG decomposition fails with `cycle_check_passed: false`
- Cycle path included in error: `["TaskA", "TaskB", "TaskC", "TaskA"]`
- Plan quarantined to `user/hitl/cyclic_dags/` with visualization


### INV-PD-05: Acceptance Criteria Testability

**Rule**: Every acceptance criterion in an MVS must be translatable to at least
one concrete test case in the plan's test strategy.

**Rationale**: Untestable acceptance criteria make it impossible to verify
implementation correctness. Indicates vague requirements.

**Enforcement**:
```rust
pub fn verify_testability(mvs: &MvsSpec, plan: &LayerablePlan) 
    -> Result<(), TestabilityError> {
    for criterion in &mvs.acceptance_criteria {
        let has_test = plan.test_strategy.test_cases.iter()
            .any(|tc| tc.description.contains(&extract_key_phrase(criterion)));
        
        if !has_test {
            return Err(TestabilityError::UntestedCriterion {
                criterion: criterion.clone(),
                suggestion: "Add test case or rephrase criterion to be testable",
            });
        }
    }
    
    Ok(())
}
```

**Testable vs Untestable Examples**:

✅ **Testable**:
- "Given a previously seen query, when searched again, then embedding retrieved from cache in <1ms"
- "Given cache at capacity, when new entry added, then LRU entry evicted"

❌ **Untestable**:
- "Search feels fast" (subjective, no concrete metric)
- "Works well with large datasets" (undefined threshold)

**Violation Consequences**:
- Plan validation warning: `W_UNTESTED_ACCEPTANCE_CRITERIA`
- Does not block plan approval, but flagged for review
- Agent logs which criteria lack tests


### INV-PD-06: Architectural Gap Resolution

**Rule**: If a plan depends on unresolved architectural gaps (GAP-001 through GAP-012),
those gaps must be marked as `required: true` in `architectural_dependencies`,
and the plan must be marked as blocked.

**Rationale**: Prevents generating plans that cannot be implemented due to missing
infrastructure. Forces sequential resolution of dependencies.

**Enforcement**:
```rust
pub fn check_gap_dependencies(mvs: &MvsSpec) -> Result<GapStatus, GapError> {
    let mut blocking_gaps = vec![];
    
    for dep in &mvs.architectural_dependencies {
        if dep.required {
            let gap_status = query_gap_registry(&dep.gap_id)?;
            if gap_status != GapStatus::Resolved {
                blocking_gaps.push((dep.gap_id.clone(), gap_status));
            }
        }
    }
    
    if !blocking_gaps.is_empty() {
        return Err(GapError::UnresolvedBlockingGaps {
            gaps: blocking_gaps,
            message: "Implement required architectural gaps before proceeding",
        });
    }
    
    Ok(GapStatus::AllResolved)
}
```

**Gap Registry Query**:
```yaml
# .nb/plan/architectural_gaps/gap_registry.yaml
gaps:
  - gap_id: GAP-001
    title: "Core Pillars Rust Crates Missing"
    status: unresolved
    blocks:
      - thought_to_project
      - proactive_intelligence
  
  - gap_id: GAP-003
    title: "Credential Leasing Not Implemented"
    status: in_progress
    blocks:
      - meeting_intelligence
```

**Violation Consequences**:
- Plan compilation fails with `E_BLOCKED_BY_GAPS`
- List of blocking gaps included in error
- User directed to implement gaps first


### INV-PD-07: Plan Title and Slug Uniqueness

**Rule**: Within a project, no two plans may have the same `slug`. Plan titles
should be unique but are not strictly enforced (slugs are canonical).

**Rationale**: Slugs are used for file paths (`.nb/plan/extensions/{slug}/concise.md`).
Collisions would overwrite existing plans.

**Enforcement**:
```rust
pub fn ensure_slug_unique(slug: &str, project_id: &str) -> Result<(), SlugError> {
    let existing_plans = list_plans_for_project(project_id)?;
    
    if existing_plans.iter().any(|p| p.slug == slug) {
        return Err(SlugError::SlugCollision {
            slug: slug.to_string(),
            existing_plan_path: format!(".nb/plan/extensions/{}/concise.md", slug),
            suggestion: format!("Use slug: {}_v2 or choose different name", slug),
        });
    }
    
    Ok(())
}
```

**Slug Generation Rules**:
1. Derived from plan title via `to_lowercase().replace(' ', '_')`
2. Strip non-alphanumeric except underscore: `[^a-z0-9_]` → `""`
3. Collapse multiple underscores: `__+` → `_`
4. Check uniqueness, append `_v2`, `_v3`, etc. if collision

**Violation Consequences**:
- Plan compilation fails with `E_SLUG_COLLISION`
- Suggests alternative slug
- User must either rename or accept versioned slug


### INV-PD-08: Confidence Threshold Enforcement

**Rule**: MVS specifications with `confidence_score < 0.70` must be flagged for
HITL review. Plans may not be compiled from low-confidence MVS without explicit
user approval.

**Rationale**: Low confidence indicates agent uncertainty about requirements.
Proceeding risks implementing the wrong thing.

**Enforcement**:
```rust
pub fn enforce_confidence_threshold(mvs: &MvsSpec, threshold: f64) 
    -> Result<ApprovalStatus, ConfidenceError> {
    if mvs.confidence_score < threshold {
        return Ok(ApprovalStatus::RequiresHitl {
            confidence: mvs.confidence_score,
            threshold,
            approval_path: format!("user/hitl/mvs_approval_queue/{}.md", mvs.mvs_id),
        });
    }
    
    Ok(ApprovalStatus::AutoApproved)
}
```

**Approval Workflow**:
1. Low-confidence MVS triggers workflow stage: `05_check_confidence`
2. Generate approval request in `user/hitl/mvs_approval_queue/{mvs_id}.md`
3. Wait for user command: `pos workflow approve {workflow_id} --stage 05_check_confidence`
4. If approved, continue to plan compilation
5. If timeout (3 days), auto-reject and archive MVS

**Violation Consequences**:
- Plan compilation paused until approval
- User notified of low confidence and specific concerns
- Timeout results in workflow cancellation


### INV-PD-09: Domain Consistency

**Rule**: All components in a plan must align with the plan's declared `domain`.
Cross-domain components require explicit justification.

**Rationale**: Keeps plans focused and prevents scope creep. Cross-domain plans
are harder to reason about and maintain.

**Enforcement**:
```rust
pub fn verify_domain_consistency(mvs: &MvsSpec) -> Result<(), DomainError> {
    let declared_domain = &mvs.domain;
    
    for component in &mvs.components {
        let inferred_domain = infer_component_domain(&component.description);
        
        if inferred_domain != *declared_domain {
            // Check for explicit justification
            if component.cross_domain_justification.is_none() {
                return Err(DomainError::CrossDomainComponent {
                    component: component.name.clone(),
                    declared: declared_domain.clone(),
                    inferred: inferred_domain,
                    suggestion: "Add cross_domain_justification field or split into multiple plans",
                });
            }
        }
    }
    
    Ok(())
}
```

**Domain Inference Heuristics**:
- Keywords in component description mapped to domains
- "cache", "mmap", "persistence" → `storage`
- "API", "HTTP", "REST" → `api`
- "embedding", "vector", "inference" → `ml_inference`

**Violation Consequences**:
- Plan validation warning: `W_CROSS_DOMAIN_COMPONENT`
- Does not block compilation, but flagged for review
- User may add justification or split plan


### INV-PD-10: Test Strategy Completeness

**Rule**: Every plan must include a `test_strategy` with:
1. At least one test case per component
2. Coverage target ≥ 80% (configurable)
3. Mix of unit and integration tests

**Rationale**: Tests are the executable specification. Incomplete test strategy
leads to untested code and regressions.

**Enforcement**:
```rust
pub fn validate_test_strategy(plan: &LayerablePlan) -> Result<(), TestError> {
    let test_strategy = &plan.test_strategy;
    
    // Check coverage target
    if test_strategy.test_coverage_target < 80.0 {
        return Err(TestError::LowCoverageTarget {
            target: test_strategy.test_coverage_target,
            minimum: 80.0,
        });
    }
    
    // Check test case distribution
    let unit_tests = test_strategy.test_cases.iter().filter(|tc| tc.type_ == "unit").count();
    let integration_tests = test_strategy.test_cases.iter().filter(|tc| tc.type_ == "integration").count();
    
    if unit_tests == 0 {
        return Err(TestError::MissingTestType { type_: "unit".to_string() });
    }
    if integration_tests == 0 {
        return Err(TestError::MissingTestType { type_: "integration".to_string() });
    }
    
    // Check component coverage
    for component in &plan.components {
        let has_test = test_strategy.test_cases.iter()
            .any(|tc| tc.name.contains(&component.name));
        
        if !has_test {
            return Err(TestError::UntestedComponent {
                component: component.name.clone(),
            });
        }
    }
    
    Ok(())
}
```

**Violation Consequences**:
- Plan validation error: `E_INCOMPLETE_TEST_STRATEGY`
- Specific missing test types or components listed
- Plan quarantined until tests added


## Invariant Verification Timeline

| Stage | Invariants Checked | Enforcement Level |
|-------|-------------------|-------------------|
| **MVS Synthesis** | INV-PD-02, INV-PD-08 | ERROR (blocks) |
| **Plan Compilation** | INV-PD-01, INV-PD-03, INV-PD-06, INV-PD-07 | ERROR (blocks) |
| **Plan Validation** | INV-PD-05, INV-PD-09, INV-PD-10 | WARNING (flags) |
| **DAG Decomposition** | INV-PD-04 | ERROR (blocks) |

## Metadata and Traceability

### Plan Metadata File
Every plan generates a `.metadata.yaml` file alongside `concise.md`:

```yaml
# .nb/plan/extensions/vector_cache/.metadata.yaml
plan_id: plan-f9a3c2b1-7d8e-4f56-9012-3456789abcde
mvs_id: mvs-a3f2b9c1-4d5e-6f78-9012-3456789abcde
mvs_path: user/inputs/mvs-a3f2b9c1.yaml
thought_id: thought-98a2f1
domain: storage
slug: vector_cache
created_at: 2026-10-04T14:23:00Z
created_by: agent_plan_architect
validation_status: valid
confidence_score: 0.92
```

### Thought Backlink
When plan is compiled, update thought metadata:

```sql
UPDATE thoughts
SET metadata = json_set(
    metadata, 
    '$.linked_plans', 
    json_array_append(
        json_extract(metadata, '$.linked_plans'), 
        '$', 
        'plan-f9a3c2b1-7d8e-4f56-9012-3456789abcde'
    )
)
WHERE id = 'thought-98a2f1';
```

## Related Documents

- `plan_synthesis_contract.json` - JSON Schema for MVS validation
- `thought_to_project_wire_contracts.yaml` - Agent RPC contracts
- `.nb/plan/architectural_gaps/gap_registry.yaml` - Gap status tracking
- `worktree_isolation_rules.md` - Invariants for ephemeral worktrees

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-10-04 | Initial invariants for thought-to-project foundation |
