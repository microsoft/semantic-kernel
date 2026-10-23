//! Agent conversation thread management

use crate::errors::{AgentError, Result};
use semantic_kernel::{ChatHistory, ChatMessageContent, ChatMessage, AuthorRole};
use std::sync::{Arc, Mutex};
use uuid::Uuid;
use chrono::{DateTime, Utc};

/// Represents a conversation thread with an agent.
/// 
/// A thread manages the conversation state, history, and lifecycle
/// for interactions with one or more agents. Threads are used to
/// maintain context across multiple message exchanges.
#[derive(Debug)]
pub struct AgentThread {
    id: String,
    chat_history: Arc<Mutex<ChatHistory>>,
    created_at: DateTime<Utc>,
    is_deleted: bool,
    metadata: std::collections::HashMap<String, String>,
}

impl AgentThread {
    /// Creates a new agent thread with a generated ID.
    pub fn new() -> Self {
        Self::with_id(Uuid::new_v4().to_string())
    }
    
    /// Creates a new agent thread with the specified ID.
    pub fn with_id(id: String) -> Self {
        Self {
            id,
            chat_history: Arc::new(Mutex::new(ChatHistory::new())),
            created_at: Utc::now(),
            is_deleted: false,
            metadata: std::collections::HashMap::new(),
        }
    }
    
    /// Gets the thread ID.
    pub fn id(&self) -> &str {
        &self.id
    }
    
    /// Gets the creation timestamp.
    pub fn created_at(&self) -> DateTime<Utc> {
        self.created_at
    }
    
    /// Gets whether the thread has been deleted.
    pub fn is_deleted(&self) -> bool {
        self.is_deleted
    }
    
    /// Marks the thread as deleted.
    pub fn delete(&mut self) {
        self.is_deleted = true;
    }
    
    /// Gets a copy of the chat history.
    pub fn get_chat_history(&self) -> ChatHistory {
        let history = self.chat_history.lock().unwrap();
        history.clone()
    }
    
    /// Adds a message to the thread's chat history.
    pub fn add_message(&mut self, message: ChatMessageContent) -> Result<()> {
        if self.is_deleted {
            return Err(AgentError::InvalidState("Thread has been deleted".to_string()));
        }
        
        let mut history = self.chat_history.lock()
            .map_err(|e| AgentError::Thread(format!("Failed to lock chat history: {}", e)))?;
        
        // Convert ChatMessageContent to ChatMessage
        let chat_message = ChatMessage::assistant(&message.content);
        history.add_message(chat_message);
        
        Ok(())
    }
    
    /// Adds a user message to the thread.
    pub fn add_user_message(&mut self, content: impl Into<String>) -> Result<()> {
        if self.is_deleted {
            return Err(AgentError::InvalidState("Thread has been deleted".to_string()));
        }
        
        let mut history = self.chat_history.lock()
            .map_err(|e| AgentError::Thread(format!("Failed to lock chat history: {}", e)))?;
        
        let message = ChatMessage::user(content.into());
        history.add_message(message);
        
        Ok(())
    }
    
    /// Adds an assistant message to the thread.
    pub fn add_assistant_message(&mut self, content: impl Into<String>) -> Result<()> {
        if self.is_deleted {
            return Err(AgentError::InvalidState("Thread has been deleted".to_string()));
        }
        
        let mut history = self.chat_history.lock()
            .map_err(|e| AgentError::Thread(format!("Failed to lock chat history: {}", e)))?;
        
        let message = ChatMessage::assistant(content.into());
        history.add_message(message);
        
        Ok(())
    }
    
    /// Adds a system message to the thread.
    pub fn add_system_message(&mut self, content: impl Into<String>) -> Result<()> {
        if self.is_deleted {
            return Err(AgentError::InvalidState("Thread has been deleted".to_string()));
        }
        
        let mut history = self.chat_history.lock()
            .map_err(|e| AgentError::Thread(format!("Failed to lock chat history: {}", e)))?;
        
        let message = ChatMessage::system(content.into());
        history.add_message(message);
        
        Ok(())
    }
    
    /// Clears the chat history.
    pub fn clear_history(&mut self) -> Result<()> {
        if self.is_deleted {
            return Err(AgentError::InvalidState("Thread has been deleted".to_string()));
        }
        
        let mut history = self.chat_history.lock()
            .map_err(|e| AgentError::Thread(format!("Failed to lock chat history: {}", e)))?;
        
        *history = ChatHistory::new();
        Ok(())
    }
    
    /// Gets the number of messages in the thread.
    pub fn message_count(&self) -> usize {
        let history = self.chat_history.lock().unwrap();
        history.messages.len()
    }
    
    /// Sets metadata for the thread.
    pub fn set_metadata(&mut self, key: String, value: String) {
        self.metadata.insert(key, value);
    }
    
    /// Gets metadata from the thread.
    pub fn get_metadata(&self, key: &str) -> Option<&String> {
        self.metadata.get(key)
    }
    
    /// Gets all metadata.
    pub fn get_all_metadata(&self) -> &std::collections::HashMap<String, String> {
        &self.metadata
    }
    
    /// Creates a snapshot of the thread state for serialization.
    pub fn create_snapshot(&self) -> ThreadSnapshot {
        let history = self.chat_history.lock().unwrap();
        ThreadSnapshot {
            id: self.id.clone(),
            created_at: self.created_at,
            is_deleted: self.is_deleted,
            message_count: history.messages.len(),
            metadata: self.metadata.clone(),
        }
    }
}

impl Default for AgentThread {
    fn default() -> Self {
        Self::new()
    }
}

impl Clone for AgentThread {
    fn clone(&self) -> Self {
        let history = self.chat_history.lock().unwrap();
        let mut new_thread = Self::with_id(format!("{}-clone", self.id));
        new_thread.created_at = self.created_at;
        new_thread.is_deleted = self.is_deleted;
        new_thread.metadata = self.metadata.clone();
        
        // Copy history
        *new_thread.chat_history.lock().unwrap() = history.clone();
        
        new_thread
    }
}

/// A serializable snapshot of thread state.
#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct ThreadSnapshot {
    pub id: String,
    pub created_at: DateTime<Utc>,
    pub is_deleted: bool,
    pub message_count: usize,
    pub metadata: std::collections::HashMap<String, String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_thread_creation() {
        let thread = AgentThread::new();
        assert!(!thread.id().is_empty());
        assert!(!thread.is_deleted());
        assert_eq!(thread.message_count(), 0);
    }
    
    #[test]
    fn test_agent_thread_with_id() {
        let thread = AgentThread::with_id("test-id".to_string());
        assert_eq!(thread.id(), "test-id");
    }
    
    #[test]
    fn test_add_messages() {
        let mut thread = AgentThread::new();
        
        thread.add_user_message("Hello").unwrap();
        assert_eq!(thread.message_count(), 1);
        
        thread.add_assistant_message("Hi there!").unwrap();
        assert_eq!(thread.message_count(), 2);
        
        thread.add_system_message("System message").unwrap();
        assert_eq!(thread.message_count(), 3);
    }
    
    #[test]
    fn test_clear_history() {
        let mut thread = AgentThread::new();
        thread.add_user_message("Hello").unwrap();
        thread.add_assistant_message("Hi").unwrap();
        assert_eq!(thread.message_count(), 2);
        
        thread.clear_history().unwrap();
        assert_eq!(thread.message_count(), 0);
    }
    
    #[test]
    fn test_delete_thread() {
        let mut thread = AgentThread::new();
        thread.add_user_message("Hello").unwrap();
        
        thread.delete();
        assert!(thread.is_deleted());
        
        // Should not be able to add messages after deletion
        let result = thread.add_user_message("After delete");
        assert!(result.is_err());
    }
    
    #[test]
    fn test_metadata() {
        let mut thread = AgentThread::new();
        
        thread.set_metadata("key1".to_string(), "value1".to_string());
        thread.set_metadata("key2".to_string(), "value2".to_string());
        
        assert_eq!(thread.get_metadata("key1"), Some(&"value1".to_string()));
        assert_eq!(thread.get_metadata("key2"), Some(&"value2".to_string()));
        assert_eq!(thread.get_metadata("key3"), None);
        
        assert_eq!(thread.get_all_metadata().len(), 2);
    }
    
    #[test]
    fn test_thread_snapshot() {
        let mut thread = AgentThread::new();
        thread.add_user_message("Hello").unwrap();
        thread.set_metadata("test".to_string(), "value".to_string());
        
        let snapshot = thread.create_snapshot();
        assert_eq!(snapshot.id, thread.id());
        assert_eq!(snapshot.message_count, 1);
        assert_eq!(snapshot.metadata.get("test"), Some(&"value".to_string()));
        assert!(!snapshot.is_deleted);
    }
    
    #[test]
    fn test_thread_clone() {
        let mut thread = AgentThread::with_id("original".to_string());
        thread.add_user_message("Hello").unwrap();
        thread.set_metadata("key".to_string(), "value".to_string());
        
        let cloned = thread.clone();
        assert_eq!(cloned.id(), "original-clone");
        assert_eq!(cloned.message_count(), 1);
        assert_eq!(cloned.get_metadata("key"), Some(&"value".to_string()));
        assert_eq!(cloned.created_at(), thread.created_at());
    }
}