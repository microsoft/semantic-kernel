//! Content types for chat messages, execution settings, and AI responses

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Represents a chat message in the conversation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    /// The role of the message author
    pub role: AuthorRole,
    /// The content of the message  
    pub content: String,
    /// Optional name for the message author
    pub name: Option<String>,
    /// Optional tool call ID if this is a tool response
    pub tool_call_id: Option<String>,
    /// Optional tool calls made by the assistant
    pub tool_calls: Option<Vec<ToolCall>>,
}

impl ChatMessage {
    /// Create a new system message
    pub fn system(content: impl Into<String>) -> Self {
        Self {
            role: AuthorRole::System,
            content: content.into(),
            name: None,
            tool_call_id: None,
            tool_calls: None,
        }
    }

    /// Create a new user message
    pub fn user(content: impl Into<String>) -> Self {
        Self {
            role: AuthorRole::User,
            content: content.into(),
            name: None,
            tool_call_id: None,
            tool_calls: None,
        }
    }

    /// Create a new assistant message
    pub fn assistant(content: impl Into<String>) -> Self {
        Self {
            role: AuthorRole::Assistant,
            content: content.into(),
            name: None,
            tool_call_id: None,
            tool_calls: None,
        }
    }

    /// Create a new tool message
    pub fn tool(content: impl Into<String>, tool_call_id: impl Into<String>) -> Self {
        Self {
            role: AuthorRole::Tool,
            content: content.into(),
            name: None,
            tool_call_id: Some(tool_call_id.into()),
            tool_calls: None,
        }
    }
}

/// The role of a chat message author
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum AuthorRole {
    /// System message
    System,
    /// User message
    User,
    /// Assistant/AI message
    Assistant,
    /// Tool message
    Tool,
}

/// Content returned from a chat completion service
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessageContent {
    /// The role of the message author
    pub role: AuthorRole,
    /// The text content of the message
    pub content: String,
    /// Optional model ID that generated this content
    pub model_id: Option<String>,
    /// Metadata for the response
    pub metadata: HashMap<String, String>,
    /// Tool calls made by the assistant
    pub tool_calls: Option<Vec<ToolCall>>,
}

impl ChatMessageContent {
    /// Create new chat message content
    pub fn new(role: AuthorRole, content: impl Into<String>) -> Self {
        Self {
            role,
            content: content.into(),
            model_id: None,
            metadata: HashMap::new(),
            tool_calls: None,
        }
    }

    /// Set the model ID
    pub fn with_model_id(mut self, model_id: impl Into<String>) -> Self {
        self.model_id = Some(model_id.into());
        self
    }

    /// Add metadata
    pub fn with_metadata(mut self, key: impl Into<String>, value: impl Into<String>) -> Self {
        self.metadata.insert(key.into(), value.into());
        self
    }

    /// Add tool calls
    pub fn with_tool_calls(mut self, tool_calls: Vec<ToolCall>) -> Self {
        self.tool_calls = Some(tool_calls);
        self
    }
}

/// Represents a tool call made by the AI
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    /// Unique identifier for this tool call
    pub id: String,
    /// Type of tool call (usually "function")
    pub r#type: String,
    /// Function call details
    pub function: FunctionCall,
}

/// Represents a function call within a tool call
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FunctionCall {
    /// Name of the function to call
    pub name: String,
    /// JSON string of arguments to pass to the function
    pub arguments: Option<String>,
}

/// Settings for controlling prompt execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PromptExecutionSettings {
    /// Maximum number of tokens to generate
    pub max_tokens: Option<u32>,
    /// Temperature for randomness control (0.0 - 2.0)
    pub temperature: Option<f32>,
    /// Top-p sampling parameter
    pub top_p: Option<f32>,
    /// Model ID to use for generation
    pub model_id: Option<String>,
    /// Tool choice setting ("none", "auto", or specific tool)
    pub tool_choice: Option<String>,
    /// Available tools for function calling
    pub tools: Option<Vec<serde_json::Value>>,
    /// Additional service-specific settings
    pub extension_data: HashMap<String, serde_json::Value>,
}

impl PromptExecutionSettings {
    /// Create new execution settings
    pub fn new() -> Self {
        Self {
            max_tokens: None,
            temperature: None,
            top_p: None,
            model_id: None,
            tool_choice: None,
            tools: None,
            extension_data: HashMap::new(),
        }
    }

    /// Set max tokens
    pub fn with_max_tokens(mut self, max_tokens: u32) -> Self {
        self.max_tokens = Some(max_tokens);
        self
    }

    /// Set temperature
    pub fn with_temperature(mut self, temperature: f32) -> Self {
        self.temperature = Some(temperature);
        self
    }

    /// Set top-p
    pub fn with_top_p(mut self, top_p: f32) -> Self {
        self.top_p = Some(top_p);
        self
    }

    /// Set model ID
    pub fn with_model_id(mut self, model_id: impl Into<String>) -> Self {
        self.model_id = Some(model_id.into());
        self
    }

    /// Set tool choice
    pub fn with_tool_choice(mut self, tool_choice: impl Into<String>) -> Self {
        self.tool_choice = Some(tool_choice.into());
        self
    }

    /// Set tools
    pub fn with_tools(mut self, tools: Vec<serde_json::Value>) -> Self {
        self.tools = Some(tools);
        self
    }
}

impl Default for PromptExecutionSettings {
    fn default() -> Self {
        Self::new()
    }
}

/// A collection of chat messages representing conversation history
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ChatHistory {
    /// The messages in the conversation
    pub messages: Vec<ChatMessage>,
}

impl ChatHistory {
    /// Create a new empty chat history
    pub fn new() -> Self {
        Self {
            messages: Vec::new(),
        }
    }

    /// Add a message to the history
    pub fn add_message(&mut self, message: ChatMessage) {
        self.messages.push(message);
    }

    /// Add a system message
    pub fn add_system_message(&mut self, content: impl Into<String>) {
        self.add_message(ChatMessage::system(content));
    }

    /// Add a user message
    pub fn add_user_message(&mut self, content: impl Into<String>) {
        self.add_message(ChatMessage::user(content));
    }

    /// Add an assistant message
    pub fn add_assistant_message(&mut self, content: impl Into<String>) {
        self.add_message(ChatMessage::assistant(content));
    }

    /// Get the number of messages
    pub fn len(&self) -> usize {
        self.messages.len()
    }

    /// Check if the history is empty
    pub fn is_empty(&self) -> bool {
        self.messages.is_empty()
    }
}

/// Streaming content chunk from a chat completion service
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StreamingChatMessageContent {
    /// The role of the message author (if this is the first chunk)
    pub role: Option<AuthorRole>,
    /// The text content chunk
    pub content: Option<String>,
    /// Optional model ID that generated this content
    pub model_id: Option<String>,
    /// Whether this is the final chunk
    pub finish_reason: Option<String>,
    /// Tool calls in this chunk
    pub tool_calls: Option<Vec<ToolCall>>,
}

impl StreamingChatMessageContent {
    /// Create a new streaming content chunk
    pub fn new(content: Option<String>) -> Self {
        Self {
            role: None,
            content,
            model_id: None,
            finish_reason: None,
            tool_calls: None,
        }
    }
    
    /// Create a chunk with role information (typically first chunk)
    pub fn with_role(mut self, role: AuthorRole) -> Self {
        self.role = Some(role);
        self
    }
    
    /// Mark this as the final chunk
    pub fn final_chunk(mut self, reason: String) -> Self {
        self.finish_reason = Some(reason);
        self
    }
}