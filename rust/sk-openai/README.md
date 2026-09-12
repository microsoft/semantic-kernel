# sk-openai

OpenAI connector for Semantic Kernel Rust, providing chat completion services.

## Features

- Chat completion integration with OpenAI's GPT models
- Full compatibility with Semantic Kernel's service abstractions
- Support for all major OpenAI API parameters (temperature, max_tokens, etc.)
- Proper error handling and API response mapping
- Message format conversion between Semantic Kernel and OpenAI formats

## Usage

### Basic Setup

```rust
use semantic_kernel::KernelBuilder;
use sk_openai::OpenAIClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Create OpenAI client with API key
    let openai_client = OpenAIClient::new("your-api-key-here")?;
    
    // Or create from environment variable
    let openai_client = OpenAIClient::from_env()?;
    
    // Create kernel with OpenAI service
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(openai_client)
        .build();
    
    // Use the kernel
    let response = kernel.invoke_prompt_async("Hello, OpenAI!").await?;
    println!("Response: {}", response);
    
    Ok(())
}
```

### Chat Completion with Settings

```rust
use semantic_kernel::{KernelBuilder, content::{ChatHistory, PromptExecutionSettings}};
use sk_openai::OpenAIClient;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    let client = OpenAIClient::with_model("your-api-key", "gpt-4")?;
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(client)
        .build();
    
    // Configure execution settings
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(150)
        .with_temperature(0.7)
        .with_model_id("gpt-4");
    
    // Build conversation
    let mut chat_history = ChatHistory::new();
    chat_history.add_system_message("You are a helpful assistant.");
    chat_history.add_user_message("What is Rust?");
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await?;
    println!("Assistant: {}", response.content);
    
    Ok(())
}
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required when using `OpenAIClient::from_env()`)

## Supported Models

- `gpt-3.5-turbo` (default)
- `gpt-4`
- `gpt-4-turbo`
- Any other OpenAI chat completion model

## Error Handling

The crate provides comprehensive error handling for:

- Missing or invalid API keys
- Network connectivity issues
- OpenAI API errors (rate limiting, invalid requests, etc.)
- JSON serialization/deserialization errors

## Dependencies

This crate uses minimal dependencies:

- `reqwest` - HTTP client for API requests
- `serde` and `serde_json` - JSON serialization
- `tokio` - Async runtime
- `semantic_kernel` - Core SK functionality

All dependencies are MIT or Apache-2.0 licensed.

## License

MIT