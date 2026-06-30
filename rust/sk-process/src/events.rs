//! Event logging system for process auditability

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::sync::Mutex;
use tokio::sync::mpsc;
use tracing::{info, debug};
use uuid::Uuid;

/// Events that can occur during process execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ProcessEvent {
    /// Process started
    ProcessStarted {
        process_id: Uuid,
        process_name: String,
        timestamp: DateTime<Utc>,
    },
    /// Process completed successfully
    ProcessCompleted {
        process_id: Uuid,
        timestamp: DateTime<Utc>,
    },
    /// Process failed
    ProcessFailed {
        process_id: Uuid,
        error: String,
        timestamp: DateTime<Utc>,
    },
    /// Process paused
    ProcessPaused {
        process_id: Uuid,
        step_name: String,
        timestamp: DateTime<Utc>,
    },
    /// Process resumed
    ProcessResumed {
        process_id: Uuid,
        step_index: usize,
        timestamp: DateTime<Utc>,
    },
    /// Step started
    StepStarted {
        process_id: Uuid,
        step_name: String,
        step_index: usize,
        timestamp: DateTime<Utc>,
    },
    /// Step completed
    StepCompleted {
        process_id: Uuid,
        step_name: String,
        step_index: usize,
        success: bool,
        output: Option<serde_json::Value>,
        timestamp: DateTime<Utc>,
    },
}

impl ProcessEvent {
    /// Get the process ID for this event
    pub fn process_id(&self) -> Uuid {
        match self {
            ProcessEvent::ProcessStarted { process_id, .. } => *process_id,
            ProcessEvent::ProcessCompleted { process_id, .. } => *process_id,
            ProcessEvent::ProcessFailed { process_id, .. } => *process_id,
            ProcessEvent::ProcessPaused { process_id, .. } => *process_id,
            ProcessEvent::ProcessResumed { process_id, .. } => *process_id,
            ProcessEvent::StepStarted { process_id, .. } => *process_id,
            ProcessEvent::StepCompleted { process_id, .. } => *process_id,
        }
    }
    
    /// Get the timestamp for this event
    pub fn timestamp(&self) -> DateTime<Utc> {
        match self {
            ProcessEvent::ProcessStarted { timestamp, .. } => *timestamp,
            ProcessEvent::ProcessCompleted { timestamp, .. } => *timestamp,
            ProcessEvent::ProcessFailed { timestamp, .. } => *timestamp,
            ProcessEvent::ProcessPaused { timestamp, .. } => *timestamp,
            ProcessEvent::ProcessResumed { timestamp, .. } => *timestamp,
            ProcessEvent::StepStarted { timestamp, .. } => *timestamp,
            ProcessEvent::StepCompleted { timestamp, .. } => *timestamp,
        }
    }
    
    /// Get a human-readable description of this event
    pub fn description(&self) -> String {
        match self {
            ProcessEvent::ProcessStarted { process_name, .. } => {
                format!("Process '{}' started", process_name)
            }
            ProcessEvent::ProcessCompleted { .. } => {
                "Process completed successfully".to_string()
            }
            ProcessEvent::ProcessFailed { error, .. } => {
                format!("Process failed: {}", error)
            }
            ProcessEvent::ProcessPaused { step_name, .. } => {
                format!("Process paused after step '{}'", step_name)
            }
            ProcessEvent::ProcessResumed { step_index, .. } => {
                format!("Process resumed from step {}", step_index)
            }
            ProcessEvent::StepStarted { step_name, .. } => {
                format!("Step '{}' started", step_name)
            }
            ProcessEvent::StepCompleted { step_name, success, .. } => {
                if *success {
                    format!("Step '{}' completed successfully", step_name)
                } else {
                    format!("Step '{}' failed", step_name)
                }
            }
        }
    }
}

/// Event log for storing and retrieving process events
pub struct EventLog {
    events: Mutex<VecDeque<ProcessEvent>>,
    max_events: usize,
    event_sender: Option<mpsc::UnboundedSender<ProcessEvent>>,
}

impl EventLog {
    /// Create a new event log
    pub fn new() -> Self {
        Self::with_capacity(1000)
    }
    
    /// Create a new event log with a specific capacity
    pub fn with_capacity(max_events: usize) -> Self {
        Self {
            events: Mutex::new(VecDeque::with_capacity(max_events)),
            max_events,
            event_sender: None,
        }
    }
    
    /// Create a new event log with an event stream sender
    pub fn with_sender(sender: mpsc::UnboundedSender<ProcessEvent>) -> Self {
        Self {
            events: Mutex::new(VecDeque::with_capacity(1000)),
            max_events: 1000,
            event_sender: Some(sender),
        }
    }
    
    /// Log an event
    pub async fn log_event(&self, event: ProcessEvent) {
        // Log to tracing
        match &event {
            ProcessEvent::ProcessStarted { process_name, process_id, .. } => {
                info!("Process started: {} ({})", process_name, process_id);
            }
            ProcessEvent::ProcessCompleted { process_id, .. } => {
                info!("Process completed: {}", process_id);
            }
            ProcessEvent::ProcessFailed { process_id, error, .. } => {
                info!("Process failed: {} - {}", process_id, error);
            }
            ProcessEvent::ProcessPaused { process_id, step_name, .. } => {
                info!("Process paused: {} after step '{}'", process_id, step_name);
            }
            ProcessEvent::ProcessResumed { process_id, step_index, .. } => {
                info!("Process resumed: {} from step {}", process_id, step_index);
            }
            ProcessEvent::StepStarted { process_id, step_name, .. } => {
                debug!("Step started: {} - '{}'", process_id, step_name);
            }
            ProcessEvent::StepCompleted { process_id, step_name, success, .. } => {
                if *success {
                    debug!("Step completed: {} - '{}'", process_id, step_name);
                } else {
                    debug!("Step failed: {} - '{}'", process_id, step_name);
                }
            }
        }
        
        // Store in memory
        {
            let mut events = self.events.lock().unwrap();
            
            // Remove old events if we've reached capacity
            while events.len() >= self.max_events {
                events.pop_front();
            }
            
            events.push_back(event.clone());
        }
        
        // Send to stream if configured
        if let Some(sender) = &self.event_sender {
            let _ = sender.send(event);
        }
    }
    
    /// Get all events for a specific process
    pub fn get_events_for_process(&self, process_id: Uuid) -> Vec<ProcessEvent> {
        let events = self.events.lock().unwrap();
        events
            .iter()
            .filter(|event| event.process_id() == process_id)
            .cloned()
            .collect()
    }
    
    /// Get the most recent events (up to limit)
    pub fn get_recent_events(&self, limit: usize) -> Vec<ProcessEvent> {
        let events = self.events.lock().unwrap();
        events
            .iter()
            .rev()
            .take(limit)
            .cloned()
            .collect()
    }
    
    /// Get all events
    pub fn get_all_events(&self) -> Vec<ProcessEvent> {
        let events = self.events.lock().unwrap();
        events.iter().cloned().collect()
    }
    
    /// Clear all events
    pub fn clear(&self) {
        let mut events = self.events.lock().unwrap();
        events.clear();
    }
    
    /// Get the number of events stored
    pub fn event_count(&self) -> usize {
        let events = self.events.lock().unwrap();
        events.len()
    }
    
    /// Export events to JSON
    pub fn export_to_json(&self) -> Result<String, serde_json::Error> {
        let events = self.get_all_events();
        serde_json::to_string_pretty(&events)
    }
    
    /// Create an event stream receiver
    pub fn create_event_stream() -> (Self, mpsc::UnboundedReceiver<ProcessEvent>) {
        let (sender, receiver) = mpsc::unbounded_channel();
        let event_log = Self::with_sender(sender);
        (event_log, receiver)
    }
}

impl Default for EventLog {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_event_log_basic_operations() {
        let event_log = EventLog::new();
        let process_id = Uuid::new_v4();
        
        // Log some events
        event_log.log_event(ProcessEvent::ProcessStarted {
            process_id,
            process_name: "test_process".to_string(),
            timestamp: Utc::now(),
        }).await;
        
        event_log.log_event(ProcessEvent::StepStarted {
            process_id,
            step_name: "step1".to_string(),
            step_index: 0,
            timestamp: Utc::now(),
        }).await;
        
        event_log.log_event(ProcessEvent::ProcessCompleted {
            process_id,
            timestamp: Utc::now(),
        }).await;
        
        // Check event count
        assert_eq!(event_log.event_count(), 3);
        
        // Get events for process
        let process_events = event_log.get_events_for_process(process_id);
        assert_eq!(process_events.len(), 3);
        
        // Get recent events
        let recent_events = event_log.get_recent_events(2);
        assert_eq!(recent_events.len(), 2);
    }
    
    #[tokio::test]
    async fn test_event_log_capacity_limit() {
        let event_log = EventLog::with_capacity(2);
        let process_id = Uuid::new_v4();
        
        // Log more events than capacity
        for i in 0..5 {
            event_log.log_event(ProcessEvent::StepStarted {
                process_id,
                step_name: format!("step{}", i),
                step_index: i,
                timestamp: Utc::now(),
            }).await;
        }
        
        // Should only have 2 events (the most recent ones)
        assert_eq!(event_log.event_count(), 2);
        
        let events = event_log.get_all_events();
        if let ProcessEvent::StepStarted { step_name, .. } = &events[0] {
            assert_eq!(step_name, "step3");
        }
        if let ProcessEvent::StepStarted { step_name, .. } = &events[1] {
            assert_eq!(step_name, "step4");
        }
    }
    
    #[tokio::test]
    async fn test_event_stream() {
        let (event_log, mut receiver) = EventLog::create_event_stream();
        let process_id = Uuid::new_v4();
        
        // Log an event
        event_log.log_event(ProcessEvent::ProcessStarted {
            process_id,
            process_name: "test_process".to_string(),
            timestamp: Utc::now(),
        }).await;
        
        // Check that event was received on stream
        let event = receiver.recv().await.unwrap();
        match event {
            ProcessEvent::ProcessStarted { process_name, .. } => {
                assert_eq!(process_name, "test_process");
            }
            _ => panic!("Expected ProcessStarted event"),
        }
    }
    
    #[test]
    fn test_event_descriptions() {
        let process_id = Uuid::new_v4();
        let timestamp = Utc::now();
        
        let event = ProcessEvent::ProcessStarted {
            process_id,
            process_name: "test_process".to_string(),
            timestamp,
        };
        assert_eq!(event.description(), "Process 'test_process' started");
        
        let event = ProcessEvent::StepCompleted {
            process_id,
            step_name: "test_step".to_string(),
            step_index: 0,
            success: true,
            output: None,
            timestamp,
        };
        assert_eq!(event.description(), "Step 'test_step' completed successfully");
        
        let event = ProcessEvent::ProcessFailed {
            process_id,
            error: "Something went wrong".to_string(),
            timestamp,
        };
        assert_eq!(event.description(), "Process failed: Something went wrong");
    }
    
    #[tokio::test]
    async fn test_export_to_json() {
        let event_log = EventLog::new();
        let process_id = Uuid::new_v4();
        
        event_log.log_event(ProcessEvent::ProcessStarted {
            process_id,
            process_name: "test_process".to_string(),
            timestamp: Utc::now(),
        }).await;
        
        let json = event_log.export_to_json().unwrap();
        assert!(json.contains("ProcessStarted"));
        assert!(json.contains("test_process"));
    }
}