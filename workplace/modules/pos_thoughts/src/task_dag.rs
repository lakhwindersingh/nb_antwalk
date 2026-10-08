use std::collections::HashMap;
use petgraph::algo::toposort;
use petgraph::graph::{DiGraph, NodeIndex};
use serde::{Deserialize, Serialize};

#[derive(Debug, thiserror::Error, PartialEq, Eq)]
pub enum TaskDagError {
    #[error("E_TASK_DAG_CYCLE_DETECTED: Circular dependency detected involving task '{0}'")]
    CycleDetected(String),

    #[error("E_TASK_DAG_NOT_FOUND: Task '{0}' not found in dependency graph")]
    TaskNotFound(String),
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PipelineTask {
    pub task_id: String,
    pub name: String,
    pub description: String,
    pub priority: i32,
    pub estimated_minutes: u32,
}

/// Petgraph-backed Acyclic Task Dependency Graph (E-THOUGHT-05)
pub struct TaskDag {
    graph: DiGraph<PipelineTask, ()>,
    node_map: HashMap<String, NodeIndex>,
}

impl Default for TaskDag {
    fn default() -> Self {
        Self::new()
    }
}

impl TaskDag {
    pub fn new() -> Self {
        Self {
            graph: DiGraph::new(),
            node_map: HashMap::new(),
        }
    }

    pub fn add_task(&mut self, task: PipelineTask) -> NodeIndex {
        let task_id = task.task_id.clone();
        let idx = self.graph.add_node(task);
        self.node_map.insert(task_id, idx);
        idx
    }

    /// Adds a dependency: `depends_on` must finish before `task_id` can begin
    pub fn add_dependency(&mut self, task_id: &str, depends_on: &str) -> Result<(), TaskDagError> {
        let child_idx = *self
            .node_map
            .get(task_id)
            .ok_or_else(|| TaskDagError::TaskNotFound(task_id.to_string()))?;

        let parent_idx = *self
            .node_map
            .get(depends_on)
            .ok_or_else(|| TaskDagError::TaskNotFound(depends_on.to_string()))?;

        // Edge direction: parent -> child (parent must be evaluated before child)
        self.graph.add_edge(parent_idx, child_idx, ());
        Ok(())
    }

    /// Produces a topologically sorted execution sequence
    pub fn topological_sort(&self) -> Result<Vec<PipelineTask>, TaskDagError> {
        match toposort(&self.graph, None) {
            Ok(indices) => {
                let sorted_tasks = indices
                    .into_iter()
                    .map(|idx| self.graph[idx].clone())
                    .collect();
                Ok(sorted_tasks)
            }
            Err(cycle) => {
                let task = &self.graph[cycle.node_id()];
                Err(TaskDagError::CycleDetected(task.task_id.clone()))
            }
        }
    }

    /// Computes parallel execution waves (tasks that can execute concurrently)
    pub fn parallel_batches(&self) -> Result<Vec<Vec<PipelineTask>>, TaskDagError> {
        let sorted = self.topological_sort()?;
        if sorted.is_empty() {
            return Ok(Vec::new());
        }

        // Calculate in-degree for each node in a local working graph
        let mut in_degrees: HashMap<NodeIndex, usize> = HashMap::new();
        for node in self.graph.node_indices() {
            in_degrees.insert(node, self.graph.neighbors_directed(node, petgraph::Direction::Incoming).count());
        }

        let mut batches = Vec::new();
        let mut processed = 0;
        let total_nodes = self.graph.node_count();

        while processed < total_nodes {
            let mut current_wave: Vec<NodeIndex> = Vec::new();
            for (&node, &deg) in &in_degrees {
                if deg == 0 {
                    current_wave.push(node);
                }
            }

            if current_wave.is_empty() {
                return Err(TaskDagError::CycleDetected("Cycle detected in wave scheduling".to_string()));
            }

            let mut wave_tasks = Vec::new();
            for &node in &current_wave {
                in_degrees.remove(&node);
                wave_tasks.push(self.graph[node].clone());
                processed += 1;

                // Decrement in-degree for outgoing neighbors
                for neighbor in self.graph.neighbors_directed(node, petgraph::Direction::Outgoing) {
                    if let Some(deg) = in_degrees.get_mut(&neighbor) {
                        if *deg > 0 {
                            *deg -= 1;
                        }
                    }
                }
            }

            batches.push(wave_tasks);
        }

        Ok(batches)
    }

    pub fn task_count(&self) -> usize {
        self.graph.node_count()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dag_topological_sort_success() {
        let mut dag = TaskDag::new();

        let t1 = PipelineTask {
            task_id: "t1".to_string(),
            name: "Core Models".to_string(),
            description: "Base structs".to_string(),
            priority: 1,
            estimated_minutes: 30,
        };
        let t2 = PipelineTask {
            task_id: "t2".to_string(),
            name: "Storage Layer".to_string(),
            description: "SQLite persistence".to_string(),
            priority: 2,
            estimated_minutes: 45,
        };
        let t3 = PipelineTask {
            task_id: "t3".to_string(),
            name: "API Endpoints".to_string(),
            description: "Axum router".to_string(),
            priority: 3,
            estimated_minutes: 60,
        };

        dag.add_task(t1);
        dag.add_task(t2);
        dag.add_task(t3);

        dag.add_dependency("t2", "t1").unwrap(); // t2 depends on t1
        dag.add_dependency("t3", "t2").unwrap(); // t3 depends on t2

        let sorted = dag.topological_sort().unwrap();
        assert_eq!(sorted[0].task_id, "t1");
        assert_eq!(sorted[1].task_id, "t2");
        assert_eq!(sorted[2].task_id, "t3");
    }

    #[test]
    fn test_dag_cycle_detection() {
        let mut dag = TaskDag::new();

        let t1 = PipelineTask { task_id: "t1".to_string(), name: "A".to_string(), description: "".to_string(), priority: 1, estimated_minutes: 10 };
        let t2 = PipelineTask { task_id: "t2".to_string(), name: "B".to_string(), description: "".to_string(), priority: 1, estimated_minutes: 10 };

        dag.add_task(t1);
        dag.add_task(t2);

        dag.add_dependency("t2", "t1").unwrap();
        dag.add_dependency("t1", "t2").unwrap(); // Circular!

        let res = dag.topological_sort();
        assert!(matches!(res, Err(TaskDagError::CycleDetected(_))));
    }

    #[test]
    fn test_parallel_batches_computation() {
        let mut dag = TaskDag::new();

        let root = PipelineTask { task_id: "root".to_string(), name: "Root".to_string(), description: "".to_string(), priority: 1, estimated_minutes: 10 };
        let b1 = PipelineTask { task_id: "b1".to_string(), name: "Branch 1".to_string(), description: "".to_string(), priority: 2, estimated_minutes: 15 };
        let b2 = PipelineTask { task_id: "b2".to_string(), name: "Branch 2".to_string(), description: "".to_string(), priority: 2, estimated_minutes: 15 };
        let leaf = PipelineTask { task_id: "leaf".to_string(), name: "Leaf".to_string(), description: "".to_string(), priority: 3, estimated_minutes: 20 };

        dag.add_task(root);
        dag.add_task(b1);
        dag.add_task(b2);
        dag.add_task(leaf);

        dag.add_dependency("b1", "root").unwrap();
        dag.add_dependency("b2", "root").unwrap();
        dag.add_dependency("leaf", "b1").unwrap();
        dag.add_dependency("leaf", "b2").unwrap();

        let waves = dag.parallel_batches().unwrap();
        assert_eq!(waves.len(), 3);
        assert_eq!(waves[0].len(), 1); // root
        assert_eq!(waves[1].len(), 2); // b1 and b2 can execute in parallel
        assert_eq!(waves[2].len(), 1); // leaf
    }
}
