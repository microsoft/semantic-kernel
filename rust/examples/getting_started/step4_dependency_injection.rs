//! Step 4: Dependency Injection
//! 
//! This example shows how to use Dependency Injection with the Semantic Kernel.
//! It demonstrates:
//! - Creating a kernel that participates in dependency injection
//! - Using plugins that depend on injected services
//! - Service provider patterns in Rust
//! - Logging integration with injected services

use anyhow::Result;
use semantic_kernel::{
    Kernel, KernelBuilder, async_trait,
    kernel::{KernelPlugin, KernelFunction},
    content::{ChatHistory, PromptExecutionSettings},
};
use sk_openai::OpenAIClient;
use std::env;
use std::collections::HashMap;
use std::sync::Arc;
use chrono::{DateTime, Utc};
use tracing::{info, warn};

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🤖 Semantic Kernel Rust - Step 4: Dependency Injection");
    println!("======================================================\n");

    // Example 1: Get kernel using dependency injection
    println!("Example 1: Kernel using Dependency Injection");
    println!("--------------------------------------------");
    
    let service_provider = build_service_provider()?;
    let kernel = service_provider.get_kernel();
    
    // Invoke the kernel with a templated prompt and stream the results
    let mut arguments = HashMap::new();
    arguments.insert("topic".to_string(), "earth when viewed from space".to_string());
    
    let prompt = render_template("What color is the {{topic}}? Provide a detailed explanation.", &arguments);
    println!("Prompt: {}", prompt);
    
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(&prompt);
    
    let settings = PromptExecutionSettings::new()
        .with_max_tokens(150);
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Response: {}\n", response.content);

    // Example 2: Plugin using dependency injection
    println!("Example 2: Plugin using Dependency Injection");
    println!("---------------------------------------------");
    
    let mut settings = PromptExecutionSettings::new()
        .with_max_tokens(150);
    settings.extension_data.insert(
        "function_choice_behavior".to_string(),
        serde_json::json!({ "type": "auto" })
    );
    
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message("Greet the current user by name.");
    
    let response = kernel.invoke_chat_async(&chat_history, Some(&settings)).await
        .map_err(|e| anyhow::anyhow!("Failed to invoke chat: {}", e))?;
    println!("Response: {}\n", response.content);

    println!("✅ Step4 example completed!");

    Ok(())
}

// ===== DEPENDENCY INJECTION SERVICE PROVIDER =====

/// Service provider that manages dependencies and provides services
struct ServiceProvider {
    user_service: Arc<dyn UserService>,
    logger_factory: Arc<dyn LoggerFactory>,
    kernel: Kernel,
}

impl ServiceProvider {
    fn get_kernel(&self) -> &Kernel {
        &self.kernel
    }
    
    fn get_user_service(&self) -> Arc<dyn UserService> {
        Arc::clone(&self.user_service)
    }
    
    fn get_logger_factory(&self) -> Arc<dyn LoggerFactory> {
        Arc::clone(&self.logger_factory)
    }
}

/// Build a service provider with all dependencies configured
fn build_service_provider() -> Result<ServiceProvider> {
    info!("Building service provider with dependency injection");
    
    // Create services
    let logger_factory: Arc<dyn LoggerFactory> = Arc::new(TracingLoggerFactory);
    let user_service: Arc<dyn UserService> = Arc::new(FakeUserService);
    
    // Create OpenAI client
    let api_key = env::var("OPENAI_API_KEY")
        .map_err(|_| anyhow::anyhow!("OPENAI_API_KEY environment variable not found"))?;
    let openai_client = OpenAIClient::new(api_key)?;
    
    // Create plugins with injected dependencies
    let time_plugin = TimeInformationPlugin::new(Arc::clone(&logger_factory));
    let user_plugin = UserInformationPlugin::new(Arc::clone(&user_service));
    
    // Build kernel with plugins
    let kernel = KernelBuilder::new()
        .add_chat_completion_service(openai_client)
        .add_plugin("TimeInformation", Box::new(time_plugin))
        .add_plugin("UserInformation", Box::new(user_plugin))
        .build();
    
    Ok(ServiceProvider {
        user_service,
        logger_factory,
        kernel,
    })
}

// ===== SERVICE INTERFACES =====

/// Trait for user service dependency
trait UserService: Send + Sync {
    fn get_current_username(&self) -> String;
}

/// Trait for logger factory dependency
trait LoggerFactory: Send + Sync {
    fn create_logger(&self, name: &str) -> Box<dyn Logger>;
}

/// Trait for logger instances
trait Logger: Send + Sync {
    fn log_info(&self, message: &str);
    fn log_warn(&self, message: &str);
}

// ===== SERVICE IMPLEMENTATIONS =====

/// Fake implementation of UserService for demonstration
struct FakeUserService;

impl UserService for FakeUserService {
    fn get_current_username(&self) -> String {
        "Bob".to_string()
    }
}

/// Tracing-based logger factory implementation
struct TracingLoggerFactory;

impl LoggerFactory for TracingLoggerFactory {
    fn create_logger(&self, name: &str) -> Box<dyn Logger> {
        Box::new(TracingLogger::new(name.to_string()))
    }
}

/// Tracing-based logger implementation
struct TracingLogger {
    name: String,
}

impl TracingLogger {
    fn new(name: String) -> Self {
        Self { name }
    }
}

impl Logger for TracingLogger {
    fn log_info(&self, message: &str) {
        info!("{}: {}", self.name, message);
    }
    
    fn log_warn(&self, message: &str) {
        warn!("{}: {}", self.name, message);
    }
}

// ===== PLUGINS WITH DEPENDENCY INJECTION =====

/// Time information plugin that uses injected logger
struct TimeInformationPlugin {
    function: GetCurrentUtcTimeFunction,
}

impl TimeInformationPlugin {
    fn new(logger_factory: Arc<dyn LoggerFactory>) -> Self {
        Self { 
            function: GetCurrentUtcTimeFunction { logger_factory }
        }
    }
}

#[async_trait]
impl KernelPlugin for TimeInformationPlugin {
    fn name(&self) -> &str {
        "TimeInformation"
    }
    
    fn description(&self) -> &str {
        "Provides current time information with logging"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct GetCurrentUtcTimeFunction {
    logger_factory: Arc<dyn LoggerFactory>,
}

#[async_trait]
impl KernelFunction for GetCurrentUtcTimeFunction {
    fn name(&self) -> &str {
        "GetCurrentUtcTime"
    }
    
    fn description(&self) -> &str {
        "Retrieves the current time in UTC"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        _arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let logger = self.logger_factory.create_logger("TimeInformation");
        
        let utc_now: DateTime<Utc> = Utc::now();
        let time_str = utc_now.format("%a, %d %b %Y %H:%M:%S GMT").to_string();
        
        logger.log_info(&format!("Returning current time {}", time_str));
        
        Ok(time_str)
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        })
    }
}

/// User information plugin that uses injected user service
struct UserInformationPlugin {
    function: GetUsernameFunction,
}

impl UserInformationPlugin {
    fn new(user_service: Arc<dyn UserService>) -> Self {
        Self { 
            function: GetUsernameFunction { user_service }
        }
    }
}

#[async_trait]
impl KernelPlugin for UserInformationPlugin {
    fn name(&self) -> &str {
        "UserInformation"
    }
    
    fn description(&self) -> &str {
        "Provides current user information"
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function as &dyn KernelFunction]
    }
}

struct GetUsernameFunction {
    user_service: Arc<dyn UserService>,
}

#[async_trait]
impl KernelFunction for GetUsernameFunction {
    fn name(&self) -> &str {
        "GetUsername"
    }
    
    fn description(&self) -> &str {
        "Retrieves the current user's name"
    }
    
    async fn invoke(
        &self,
        _kernel: &Kernel,
        _arguments: &HashMap<String, String>,
    ) -> semantic_kernel::Result<String> {
        let username = self.user_service.get_current_username();
        Ok(username)
    }
    
    fn get_json_schema(&self) -> serde_json::Value {
        serde_json::json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        })
    }
}

// ===== HELPER FUNCTIONS =====

/// Render a template with the given arguments
fn render_template(template: &str, arguments: &HashMap<String, String>) -> String {
    let mut rendered = template.to_string();
    for (key, value) in arguments {
        let placeholder = format!("{{{{{}}}}}", key);
        rendered = rendered.replace(&placeholder, value);
    }
    rendered
}

/// Stream a prompt response with short token limit
async fn stream_prompt(kernel: &Kernel, prompt: &str) -> Result<()> {
    let mut chat_history = ChatHistory::new();
    chat_history.add_user_message(prompt);
    
    // Get the chat completion service and stream
    if let Some(service) = kernel.services().get_chat_completion_service() {
        let mut stream = service.get_streaming_chat_message_contents(&chat_history.messages, None).await
            .map_err(|e| anyhow::anyhow!("Failed to get streaming content: {}", e))?;
        
        use futures::StreamExt;
        while let Some(chunk) = stream.next().await {
            match chunk {
                Ok(content) => {
                    if let Some(text) = content.content {
                        print!("{}", text);
                    }
                },
                Err(e) => eprintln!("\nStreaming error: {}", e),
            }
        }
    }
    
    Ok(())
}