# Installation Guide 🚀

This guide will help you get started with Semantic Kernel Rust, from basic setup to running your first AI-powered applications.

## Prerequisites

### System Requirements
- **Rust** 1.70+ (with Cargo)
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 2GB+ RAM recommended
- **Network**: Internet connection for downloading dependencies and API access

### Install Rust
If you don't have Rust installed:

```bash
# Install Rust and Cargo
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Restart your terminal or source the environment
source ~/.cargo/env

# Verify installation
rustc --version
cargo --version
```

## Quick Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd semantic-kernel-rust
```

### 2. Build the Project
```bash
# Build all crates (this may take a few minutes on first run)
cargo build

# Verify build success
echo "✅ Build completed successfully!"
```

### 3. Set Up Environment Variables
Create a `.env` file in the project root:

```bash
# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=your-openai-api-key-here" > .env

# Optional: Set up other API keys
echo "BING_API_KEY=your-bing-api-key" >> .env
echo "GOOGLE_API_KEY=your-google-api-key" >> .env
```

### 4. Test Your Installation
```bash
# Run a basic example with mock services (no API key needed)
cd semantic_kernel
cargo run --example hello_prompt

# Test with OpenAI (requires API key)
cd ../examples/getting_started
cargo run --bin step1_create_kernel
```

## Example Walkthroughs

### Example 1: Hello World with OpenAI

**File**: `examples/basic_hello.rs`
```rust
use semantic_kernel::{KernelBuilder, content::ChatHistory};
use sk_openai::OpenAIConfig;
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    // Load environment variables
    dotenv::dotenv().ok();
    
    let api_key = env::var("OPENAI_API_KEY")
        .expect("OPENAI_API_KEY environment variable not set");
    
    // Create OpenAI configuration
    let openai_config = OpenAIConfig::new(&api_key)?;
    
    // Build kernel with OpenAI service
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(openai_config.build())
        .build();
    
    println!("🤖 Semantic Kernel Rust - Hello OpenAI!");
    println!("==========================================");
    
    // Simple prompt
    let response = kernel.invoke_prompt_async(
        "Hello! Please introduce yourself and tell me one fascinating fact about AI."
    ).await?;
    
    println!("🤖 AI Response:");
    println!("{}", response);
    
    // Interactive chat
    let mut chat_history = ChatHistory::new();
    chat_history.add_system_message("You are a helpful assistant specialized in Rust programming.");
    chat_history.add_user_message("What makes Rust special for systems programming?");
    
    let chat_response = kernel.invoke_chat_async(&chat_history, None).await?;
    println!("\n💬 Chat Response:");
    println!("{}", chat_response.content);
    
    println!("\n✅ Example completed!");
    Ok(())
}
```

**Run it:**
```bash
# Add to examples/getting_started/Cargo.toml:
[[bin]]
name = "basic_hello"
path = "basic_hello.rs"

# Then run:
cd examples/getting_started
cargo run --bin basic_hello
```

### Example 2: AI Agent with Personality

**File**: `examples/personality_agent.rs`
```rust
use semantic_kernel::{KernelBuilder};
use sk_openai::OpenAIConfig;
use sk_agent::{ChatCompletionAgent, AgentExecutionSettings};
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    dotenv::dotenv().ok();
    let api_key = env::var("OPENAI_API_KEY")?;
    
    // Create kernel
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(OpenAIConfig::new(&api_key)?.build())
        .build();
    
    // Create an agent with personality
    let mut agent = ChatCompletionAgent::new(
        "CodeMentor",
        "You are a wise and patient programming mentor who explains complex topics \
         with simple analogies. You always encourage learning and provide practical examples.",
        &kernel
    )?;
    
    println!("🧙‍♂️ Meet CodeMentor - Your AI Programming Mentor");
    println!("================================================");
    
    // Conversation topics
    let questions = vec![
        "What is ownership in Rust and why is it important?",
        "How do I handle errors in Rust programs?",
        "Can you explain async/await in simple terms?",
    ];
    
    for (i, question) in questions.iter().enumerate() {
        println!("\n📝 Question {}: {}", i + 1, question);
        
        let response = agent.invoke_async(question).await?;
        println!("🧙‍♂️ CodeMentor: {}", response.content);
        
        // Add a separator for readability
        if i < questions.len() - 1 {
            println!("\n" + &"-".repeat(50));
        }
    }
    
    println!("\n✅ Mentoring session complete!");
    Ok(())
}
```

### Example 3: Multi-Agent Collaboration

**File**: `examples/team_collaboration.rs`
```rust
use semantic_kernel::KernelBuilder;
use sk_openai::OpenAIConfig;
use sk_agent::{ChatCompletionAgent, AgentThread};
use std::env;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error + Send + Sync>> {
    dotenv::dotenv().ok();
    let api_key = env::var("OPENAI_API_KEY")?;
    
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(OpenAIConfig::new(&api_key)?.build())
        .build();
    
    // Create a team of specialists
    let mut architect = ChatCompletionAgent::new(
        "SystemArchitect",
        "You are a senior software architect who designs scalable systems. \
         Focus on high-level design patterns and architecture decisions.",
        &kernel
    )?;
    
    let mut developer = ChatCompletionAgent::new(
        "RustDeveloper", 
        "You are an expert Rust developer who writes efficient, safe code. \
         Focus on implementation details and best practices.",
        &kernel
    )?;
    
    let mut reviewer = ChatCompletionAgent::new(
        "CodeReviewer",
        "You are a meticulous code reviewer who ensures quality and security. \
         Focus on potential issues and improvements.",
        &kernel
    )?;
    
    println!("👥 AI Development Team Collaboration");
    println!("===================================");
    
    let project_brief = "Design and implement a thread-safe cache system in Rust \
                        that can handle high concurrent load with automatic cleanup.";
    
    println!("📋 Project Brief: {}", project_brief);
    
    // Architecture Phase
    println!("\n🏗️ Architecture Phase");
    println!("---------------------");
    let arch_response = architect.invoke_async(&format!(
        "As a system architect, design a high-level architecture for: {}", 
        project_brief
    )).await?;
    println!("🏗️ Architect: {}", arch_response.content);
    
    // Development Phase  
    println!("\n💻 Development Phase");
    println!("-------------------");
    let dev_response = developer.invoke_async(&format!(
        "Based on this architecture: '{}', implement a Rust code structure with key types and traits.",
        arch_response.content.chars().take(200).collect::<String>()
    )).await?;
    println!("💻 Developer: {}", dev_response.content);
    
    // Review Phase
    println!("\n🔍 Review Phase");
    println!("--------------");
    let review_response = reviewer.invoke_async(&format!(
        "Review this Rust implementation for potential issues: '{}'",
        dev_response.content.chars().take(300).collect::<String>()
    )).await?;
    println!("🔍 Reviewer: {}", review_response.content);
    
    println!("\n✅ Team collaboration complete!");
    Ok(())
}
```

## Framework-Specific Examples

### Vector Search & RAG
```bash
# Set up local Qdrant (optional - examples work with in-memory by default)
docker run -p 6333:6333 qdrant/qdrant

# Run vector search examples
cd examples/getting_started_with_vector_stores
cargo run --bin step01_ingest_data       # Data ingestion
cargo run --bin step02_vector_search     # Similarity search
cargo run --bin step04_use_dynamicdatamodel  # Dynamic schemas

# RAG (Retrieval-Augmented Generation)
cd ../getting_started_with_text_search
cargo run --bin step04_search_with_rag
```

### Business Process Automation
```bash
cd examples/getting_started_with_processes

# Basic process orchestration
cargo run --bin step00_processes

# Real-world business workflows
cargo run --bin account_opening    # Bank account opening process
cargo run --bin food_preparation   # Restaurant workflow
cargo run --bin map_reduce         # Parallel data processing
```

### Advanced Agent Orchestration
```bash
cd examples/getting_started_with_agents

# Multi-agent patterns
cargo run --bin step06_concurrent        # Parallel agent execution
cargo run --bin step07_sequential        # Pipeline workflows
cargo run --bin step08_handoff          # Intelligent routing
cargo run --bin step10_multiagent_declarative  # YAML-based workflows
```

## Troubleshooting

### Common Issues

#### 1. Build Failures
```bash
# Clean and rebuild
cargo clean
cargo build

# Update Rust toolchain
rustup update stable
```

#### 2. OpenAI API Issues
```bash
# Check API key format
echo $OPENAI_API_KEY | wc -c  # Should be ~51 characters for OpenAI

# Test API key manually
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-3.5-turbo","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
     https://api.openai.com/v1/chat/completions
```

#### 3. Network/Proxy Issues
```bash
# For corporate environments
export HTTPS_PROXY=http://your-proxy:port
export HTTP_PROXY=http://your-proxy:port

# Skip SSL verification (only if needed)
export RUSTFLAGS="-C target-feature=-crt-static"
```

#### 4. Performance Issues
```bash
# Build with optimizations
cargo build --release

# Run with release mode
cargo run --release --bin your_example
```

### Getting Help

1. **Check Examples**: Look at the comprehensive examples in each framework directory
2. **Read Documentation**: Each crate has detailed documentation with `cargo doc --open`
3. **Enable Logging**: Set `RUST_LOG=debug` for detailed execution logs
4. **Mock Services**: All examples can run with mock services for testing without API keys

## Next Steps

### Learn by Example Categories

1. **Beginners**: Start with `examples/getting_started/`
2. **AI Agents**: Explore `examples/getting_started_with_agents/`
3. **Business Processes**: Try `examples/getting_started_with_processes/`
4. **Search & RAG**: Dive into `examples/getting_started_with_text_search/`
5. **Vector Databases**: Work with `examples/getting_started_with_vector_stores/`

### Advanced Topics

- **Custom Plugins**: Learn macro-based plugin development
- **Performance Optimization**: Built-in benchmarking and monitoring
- **Production Deployment**: Enterprise patterns and best practices
- **Multi-Agent Workflows**: YAML-declarative agent orchestration

### API Key Setup for Advanced Examples

```bash
# Required for full functionality
OPENAI_API_KEY=sk-...           # OpenAI GPT models
BING_API_KEY=...               # Bing search (optional)
GOOGLE_API_KEY=...             # Google search (optional)
QDRANT_URL=http://localhost:6333  # Qdrant vector DB (optional)
```

---

**Ready to build AI applications with Rust?** Start with the basic examples and gradually explore the advanced frameworks! 🚀

For more details, see the main [README.md](README.md) and individual crate documentation.