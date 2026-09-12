//! Execution tracing for plans and function calls
//! 
//! Provides detailed execution traces compatible with .NET Semantic Kernel format

use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};

/// Complete execution trace for a plan or operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionTrace {
    /// Unique identifier for this execution
    pub execution_id: String,
    /// Identifier of the plan being executed
    pub plan_id: String,
    /// Timestamp when execution started
    pub start_time: DateTime<Utc>,
    /// Timestamp when execution completed (if finished)
    pub end_time: Option<DateTime<Utc>>,
    /// Sequence of events that occurred during execution
    pub events: Vec<TraceEvent>,
    /// Additional metadata for the trace
    pub metadata: HashMap<String, String>,
}

/// Events that can occur during plan execution
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", content = "data")]
pub enum TraceEvent {
    /// Plan execution started
    PlanStarted {
        plan_id: String,
        description: String,
        step_count: usize,
    },
    /// Plan execution completed
    PlanCompleted {
        success: bool,
        output: String,
        error: Option<String>,
    },
    /// Function was called
    FunctionCalled(FunctionCallTrace),
    /// Function execution completed
    FunctionCompleted {
        function_call_id: String,
        success: bool,
        output: String,
        error: Option<String>,
    },
    /// Planning process started (for planners)
    PlanningStarted {
        goal: String,
        available_functions: Vec<String>,
    },
    /// Planning process completed
    PlanningCompleted {
        success: bool,
        plan_id: Option<String>,
        error: Option<String>,
    },
    /// Custom event with arbitrary data
    CustomEvent {
        name: String,
        data: serde_json::Value,
    },
}

/// Detailed trace of a function call
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionCallTrace {
    /// Unique identifier for this function call
    pub id: String,
    /// Name of the plugin containing the function
    pub plugin_name: String,
    /// Name of the function being called
    pub function_name: String,
    /// Arguments passed to the function
    pub arguments: HashMap<String, String>,
    /// Timestamp when the call was made
    pub timestamp: DateTime<Utc>,
}

impl ExecutionTrace {
    /// Create a new execution trace
    pub fn new(execution_id: String, plan_id: String) -> Self {
        Self {
            execution_id,
            plan_id,
            start_time: Utc::now(),
            end_time: None,
            events: Vec::new(),
            metadata: HashMap::new(),
        }
    }

    /// Add an event to the trace
    pub fn add_event(&mut self, event: TraceEvent) {
        self.events.push(event);
    }

    /// Mark the trace as completed
    pub fn complete(&mut self) {
        self.end_time = Some(Utc::now());
    }

    /// Add metadata to the trace
    pub fn add_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }

    /// Get the duration of the execution if completed
    pub fn duration_ms(&self) -> Option<i64> {
        self.end_time.map(|end| (end - self.start_time).num_milliseconds())
    }

    /// Convert to JSON format compatible with .NET Semantic Kernel
    pub fn to_dotnet_format(&self) -> serde_json::Value {
        serde_json::json!({
            "executionId": self.execution_id,
            "planId": self.plan_id,
            "startTime": self.start_time.to_rfc3339(),
            "endTime": self.end_time.map(|t| t.to_rfc3339()),
            "durationMs": self.duration_ms(),
            "events": self.events.iter().map(|e| self.event_to_dotnet_format(e)).collect::<Vec<_>>(),
            "metadata": self.metadata
        })
    }

    fn event_to_dotnet_format(&self, event: &TraceEvent) -> serde_json::Value {
        match event {
            TraceEvent::PlanStarted { plan_id, description, step_count } => {
                serde_json::json!({
                    "type": "PlanStarted",
                    "timestamp": Utc::now().to_rfc3339(),
                    "planId": plan_id,
                    "description": description,
                    "stepCount": step_count
                })
            }
            TraceEvent::PlanCompleted { success, output, error } => {
                serde_json::json!({
                    "type": "PlanCompleted",
                    "timestamp": Utc::now().to_rfc3339(),
                    "success": success,
                    "output": output,
                    "error": error
                })
            }
            TraceEvent::FunctionCalled(call_trace) => {
                serde_json::json!({
                    "type": "FunctionCalled",
                    "timestamp": call_trace.timestamp.to_rfc3339(),
                    "functionCallId": call_trace.id,
                    "pluginName": call_trace.plugin_name,
                    "functionName": call_trace.function_name,
                    "arguments": call_trace.arguments
                })
            }
            TraceEvent::FunctionCompleted { function_call_id, success, output, error } => {
                serde_json::json!({
                    "type": "FunctionCompleted",
                    "timestamp": Utc::now().to_rfc3339(),
                    "functionCallId": function_call_id,
                    "success": success,
                    "output": output,
                    "error": error
                })
            }
            TraceEvent::PlanningStarted { goal, available_functions } => {
                serde_json::json!({
                    "type": "PlanningStarted",
                    "timestamp": Utc::now().to_rfc3339(),
                    "goal": goal,
                    "availableFunctions": available_functions
                })
            }
            TraceEvent::PlanningCompleted { success, plan_id, error } => {
                serde_json::json!({
                    "type": "PlanningCompleted",
                    "timestamp": Utc::now().to_rfc3339(),
                    "success": success,
                    "planId": plan_id,
                    "error": error
                })
            }
            TraceEvent::CustomEvent { name, data } => {
                serde_json::json!({
                    "type": "CustomEvent",
                    "timestamp": Utc::now().to_rfc3339(),
                    "name": name,
                    "data": data
                })
            }
        }
    }

    /// Get all function calls from the trace
    pub fn get_function_calls(&self) -> Vec<&FunctionCallTrace> {
        self.events
            .iter()
            .filter_map(|event| match event {
                TraceEvent::FunctionCalled(call_trace) => Some(call_trace),
                _ => None,
            })
            .collect()
    }

    /// Get the success rate of function calls
    pub fn success_rate(&self) -> f64 {
        let mut total_calls = 0;
        let mut successful_calls = 0;

        for event in &self.events {
            if let TraceEvent::FunctionCompleted { success, .. } = event {
                total_calls += 1;
                if *success {
                    successful_calls += 1;
                }
            }
        }

        if total_calls == 0 {
            1.0
        } else {
            successful_calls as f64 / total_calls as f64
        }
    }
}

impl FunctionCallTrace {
    /// Create a new function call trace
    pub fn new(
        plugin_name: String,
        function_name: String,
        arguments: HashMap<String, String>,
    ) -> Self {
        Self {
            id: uuid::Uuid::new_v4().to_string(),
            plugin_name,
            function_name,
            arguments,
            timestamp: Utc::now(),
        }
    }

    /// Get the full function name (plugin.function)
    pub fn full_function_name(&self) -> String {
        format!("{}.{}", self.plugin_name, self.function_name)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_execution_trace_creation() {
        let trace = ExecutionTrace::new("exec-123".to_string(), "plan-456".to_string());
        
        assert_eq!(trace.execution_id, "exec-123");
        assert_eq!(trace.plan_id, "plan-456");
        assert!(trace.events.is_empty());
        assert!(trace.end_time.is_none());
    }

    #[test]
    fn test_add_event() {
        let mut trace = ExecutionTrace::new("exec-123".to_string(), "plan-456".to_string());
        
        trace.add_event(TraceEvent::PlanStarted {
            plan_id: "plan-456".to_string(),
            description: "Test plan".to_string(),
            step_count: 2,
        });

        assert_eq!(trace.events.len(), 1);
        if let TraceEvent::PlanStarted { plan_id, description, step_count } = &trace.events[0] {
            assert_eq!(plan_id, "plan-456");
            assert_eq!(description, "Test plan");
            assert_eq!(*step_count, 2);
        } else {
            panic!("Expected PlanStarted event");
        }
    }

    #[test]
    fn test_complete_trace() {
        let mut trace = ExecutionTrace::new("exec-123".to_string(), "plan-456".to_string());
        assert!(trace.end_time.is_none());
        
        trace.complete();
        assert!(trace.end_time.is_some());
        assert!(trace.duration_ms().is_some());
        assert!(trace.duration_ms().unwrap() >= 0);
    }

    #[test]
    fn test_function_call_trace() {
        let mut args = HashMap::new();
        args.insert("input".to_string(), "test".to_string());
        
        let call_trace = FunctionCallTrace::new(
            "TestPlugin".to_string(),
            "test_function".to_string(),
            args,
        );

        assert!(!call_trace.id.is_empty());
        assert_eq!(call_trace.plugin_name, "TestPlugin");
        assert_eq!(call_trace.function_name, "test_function");
        assert_eq!(call_trace.full_function_name(), "TestPlugin.test_function");
        assert_eq!(call_trace.arguments.get("input"), Some(&"test".to_string()));
    }

    #[test]
    fn test_dotnet_format_conversion() {
        let mut trace = ExecutionTrace::new("exec-123".to_string(), "plan-456".to_string());
        
        trace.add_event(TraceEvent::PlanStarted {
            plan_id: "plan-456".to_string(),
            description: "Test plan".to_string(),
            step_count: 1,
        });

        let dotnet_format = trace.to_dotnet_format();
        
        assert_eq!(dotnet_format["executionId"], "exec-123");
        assert_eq!(dotnet_format["planId"], "plan-456");
        assert!(dotnet_format["events"].is_array());
        assert_eq!(dotnet_format["events"].as_array().unwrap().len(), 1);
    }

    #[test]
    fn test_success_rate_calculation() {
        let mut trace = ExecutionTrace::new("exec-123".to_string(), "plan-456".to_string());
        
        // Add successful function completion
        trace.add_event(TraceEvent::FunctionCompleted {
            function_call_id: "call-1".to_string(),
            success: true,
            output: "success".to_string(),
            error: None,
        });

        // Add failed function completion
        trace.add_event(TraceEvent::FunctionCompleted {
            function_call_id: "call-2".to_string(),
            success: false,
            output: "".to_string(),
            error: Some("error".to_string()),
        });

        assert_eq!(trace.success_rate(), 0.5); // 1 out of 2 succeeded
    }

    #[test]
    fn test_get_function_calls() {
        let mut trace = ExecutionTrace::new("exec-123".to_string(), "plan-456".to_string());
        
        let call_trace = FunctionCallTrace::new(
            "TestPlugin".to_string(),
            "test_function".to_string(),
            HashMap::new(),
        );

        trace.add_event(TraceEvent::FunctionCalled(call_trace.clone()));
        trace.add_event(TraceEvent::PlanStarted {
            plan_id: "plan-456".to_string(),
            description: "Test plan".to_string(),
            step_count: 1,
        });

        let function_calls = trace.get_function_calls();
        assert_eq!(function_calls.len(), 1);
        assert_eq!(function_calls[0].plugin_name, "TestPlugin");
        assert_eq!(function_calls[0].function_name, "test_function");
    }
}