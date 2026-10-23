//! Integration tests for OpenAI connector

use sk_openai::{OpenAIClient, OpenAIError};
use semantic_kernel::{
    KernelBuilder,
    content::ChatHistory,
};

#[test]
fn test_openai_client_integration_with_kernel() {
    // Test that OpenAI client can be integrated with semantic kernel
    let client = OpenAIClient::new("test-api-key").unwrap();
    
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(client)
        .build();
    
    // Verify the service was registered
    let service = kernel.services().get_chat_completion_service();
    assert!(service.is_some());
    
    let service = service.unwrap();
    assert_eq!(service.service_type(), "ChatCompletion,Embedding");
    assert_eq!(service.attributes().get("provider").unwrap(), "openai");
}

#[test]
fn test_execution_settings_applied_correctly() {
    use sk_openai::models::{ChatCompletionRequest, ChatMessage};
    
    // Test that execution settings are properly converted to OpenAI request parameters
    let messages = vec![ChatMessage::user("Hello!")];
    let mut request = ChatCompletionRequest::new("gpt-3.5-turbo", messages);
    
    // Apply settings similar to how the client does it
    request = request
        .with_max_tokens(150)
        .with_temperature(0.7)
        .with_top_p(0.9);
    
    assert_eq!(request.max_tokens, Some(150));
    assert_eq!(request.temperature, Some(0.7));
    assert_eq!(request.top_p, Some(0.9));
    assert_eq!(request.model, "gpt-3.5-turbo");
}

#[test]
fn test_error_handling() {
    // Test various error scenarios
    
    // Empty API key
    let result = OpenAIClient::new("");
    assert!(matches!(result, Err(OpenAIError::MissingApiKey)));
    
    // Missing environment variable
    std::env::remove_var("OPENAI_API_KEY");
    let result = OpenAIClient::from_env();
    assert!(matches!(result, Err(OpenAIError::MissingApiKey)));
}

#[test]
fn test_message_format_compatibility() {
    use semantic_kernel::content::ChatMessage;
    
    // Test that our message format is compatible with OpenAI's expected format
    let sk_messages = vec![
        ChatMessage::system("You are a helpful assistant."),
        ChatMessage::user("Hello!"),
        ChatMessage::assistant("Hi there! How can I help you?"),
    ];
    
    // Convert to OpenAI format
    let openai_messages: Vec<sk_openai::models::ChatMessage> = sk_messages
        .iter()
        .map(|msg| OpenAIClient::convert_sk_message_to_openai(msg))
        .collect();
    
    assert_eq!(openai_messages.len(), 3);
    assert_eq!(openai_messages[0].role, "system");
    assert_eq!(openai_messages[1].role, "user");
    assert_eq!(openai_messages[2].role, "assistant");
    
    // Verify content is preserved
    assert_eq!(openai_messages[0].content, "You are a helpful assistant.");
    assert_eq!(openai_messages[1].content, "Hello!");
    assert_eq!(openai_messages[2].content, "Hi there! How can I help you?");
}

#[tokio::test]
async fn test_chat_history_integration() {
    // Test that chat history works correctly with the OpenAI client
    let client = OpenAIClient::new("test-key").unwrap();
    let _kernel = KernelBuilder::new()
        .add_chat_completion_service(client)
        .build();
    
    let mut chat_history = ChatHistory::new();
    chat_history.add_system_message("You are a test assistant.");
    chat_history.add_user_message("Hello!");
    
    // The actual API call would fail with a fake key, but we can test the setup
    assert_eq!(chat_history.len(), 2);
    assert!(!chat_history.is_empty());
}