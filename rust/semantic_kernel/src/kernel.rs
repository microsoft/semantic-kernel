//! Core Kernel implementation providing AI orchestration capabilities

use std::collections::HashMap;
use std::sync::Arc;
use crate::services::ServiceProvider;
use crate::content::{ChatHistory, ChatMessageContent, PromptExecutionSettings};
use crate::async_trait;

/// The core Kernel providing AI orchestration and service management
pub struct Kernel {
    /// Service provider for dependency injection
    services: Arc<ServiceProvider>,
    /// Plugin collection
    plugins: HashMap<String, Box<dyn KernelPlugin>>,
    /// Ambient data stored in the kernel
    data: HashMap<String, String>,
}

impl Kernel {
    /// Create a new kernel with the given service provider
    pub fn new(services: ServiceProvider) -> Self {
        Self {
            services: Arc::new(services),
            plugins: HashMap::new(),
            data: HashMap::new(),
        }
    }

    /// Get the service provider
    pub fn services(&self) -> &ServiceProvider {
        &self.services
    }

    /// Add ambient data to the kernel
    pub fn add_data(&mut self, key: impl Into<String>, value: impl Into<String>) {
        self.data.insert(key.into(), value.into());
    }

    /// Get ambient data from the kernel
    pub fn get_data(&self, key: &str) -> Option<&String> {
        self.data.get(key)
    }

    /// Invoke a prompt using the configured chat completion service
    pub async fn invoke_prompt_async(&self, prompt: &str) -> crate::Result<String> {
        let mut chat_history = ChatHistory::new();
        chat_history.add_user_message(prompt);
        
        let result = self.invoke_chat_async(&chat_history, None).await?;
        Ok(result.content)
    }

    /// Invoke a prompt with chat history
    pub async fn invoke_chat_async(
        &self,
        chat_history: &ChatHistory,
        execution_settings: Option<&PromptExecutionSettings>,
    ) -> crate::Result<ChatMessageContent> {
        // Get chat completion service from the service provider
        if let Some(service) = self.services.get_chat_completion_service() {
            return service.get_chat_message_content(&chat_history.messages, execution_settings).await;
        }
        
        // Fallback to mock response if no service is configured
        let last_message = chat_history.messages.last()
            .map(|m| m.content.as_str())
            .unwrap_or("Hello");
            
        Ok(ChatMessageContent::new(
            crate::content::AuthorRole::Assistant,
            format!("Echo: {last_message}"),
        ))
    }

    /// Add a plugin to the kernel
    pub fn add_plugin(&mut self, name: impl Into<String>, plugin: Box<dyn KernelPlugin>) {
        self.plugins.insert(name.into(), plugin);
    }

    /// Add a semantic function from a prompt template
    pub fn add_semantic_function(&mut self, name: impl Into<String>, prompt: impl Into<String>, description: Option<String>) {
        let name_str = name.into();
        let semantic_function = SemanticFunction::new(name_str.clone(), prompt.into(), description);
        let plugin = Box::new(SemanticFunctionPlugin::new(semantic_function));
        self.add_plugin(name_str, plugin);
    }

    /// Get a plugin by name
    pub fn get_plugin(&self, name: &str) -> Option<&dyn KernelPlugin> {
        self.plugins.get(name).map(|p| p.as_ref())
    }

    /// Create a new kernel builder
    pub fn create_builder() -> KernelBuilder {
        KernelBuilder::new()
    }
}

/// Trait for kernel plugins
#[async_trait]
pub trait KernelPlugin: Send + Sync {
    /// Get the plugin name
    fn name(&self) -> &str;
    
    /// Get the plugin description
    fn description(&self) -> &str;
    
    /// Get available functions in this plugin
    fn functions(&self) -> Vec<&dyn KernelFunction>;
}

/// Trait for kernel functions
#[async_trait]
pub trait KernelFunction: Send + Sync {
    /// Get the function name
    fn name(&self) -> &str;
    
    /// Get the function description
    fn description(&self) -> &str;
    
    /// Execute the function
    async fn invoke(&self, kernel: &Kernel, arguments: &HashMap<String, String>) -> crate::Result<String>;
    
    /// Get JSON schema for function calling (optional, default implementation provided)
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

/// Builder for creating Kernel instances
pub struct KernelBuilder {
    services_builder: crate::services::ServiceProviderBuilder,
    plugins: HashMap<String, Box<dyn KernelPlugin>>,
}

impl KernelBuilder {
    /// Create a new kernel builder
    pub fn new() -> Self {
        Self {
            services_builder: crate::services::ServiceProviderBuilder::new(),
            plugins: HashMap::new(),
        }
    }

    /// Add a service to the kernel
    pub fn add_service<T: 'static + Send + Sync>(mut self, service: T) -> Self {
        self.services_builder = self.services_builder.add_service(service);
        self
    }

    /// Add a keyed service to the kernel
    pub fn add_keyed_service<T: 'static + Send + Sync>(
        mut self,
        key: impl Into<String>,
        service: T,
    ) -> Self {
        self.services_builder = self.services_builder.add_keyed_service(key.into(), service);
        self
    }

    /// Add a chat completion service
    pub fn add_chat_completion_service<T>(mut self, service: T) -> Self
    where
        T: crate::services::ChatCompletionService + 'static,
    {
        self.services_builder = self.services_builder.add_chat_completion_service(service);
        self
    }

    /// Add a plugin to the kernel
    pub fn add_plugin(mut self, name: impl Into<String>, plugin: Box<dyn KernelPlugin>) -> Self {
        self.plugins.insert(name.into(), plugin);
        self
    }

    /// Build the kernel
    pub fn build(self) -> Kernel {
        let services = self.services_builder.build();
        let mut kernel = Kernel::new(services);
        
        // Add plugins
        for (name, plugin) in self.plugins {
            kernel.add_plugin(name, plugin);
        }
        
        kernel
    }
}

impl Default for KernelBuilder {
    fn default() -> Self {
        Self::new()
    }
}

/// A semantic function that executes a prompt template
#[derive(Debug, Clone)]
pub struct SemanticFunction {
    pub name: String,
    pub description: String,
    pub prompt_template: String,
}

impl SemanticFunction {
    /// Create a new semantic function
    pub fn new(name: String, prompt_template: String, description: Option<String>) -> Self {
        Self {
            name,
            description: description.unwrap_or_else(|| "Semantic function".to_string()),
            prompt_template,
        }
    }

    /// Load a semantic function from a prompt file
    pub fn from_prompt_file(path: &std::path::Path) -> crate::Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| format!("Failed to read prompt file: {}", e))?;
        
        let name = path.file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("semantic_function")
            .to_string();
            
        Ok(Self::new(name, content, None))
    }

    /// Load a semantic function from a YAML file
    pub fn from_yaml_file(path: &std::path::Path) -> crate::Result<Self> {
        let content = std::fs::read_to_string(path)
            .map_err(|e| format!("Failed to read YAML file: {}", e))?;
        
        // For now, treat YAML as simple prompt template
        // In a real implementation, we'd parse the YAML for metadata
        let name = path.file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("semantic_function")
            .to_string();
            
        Ok(Self::new(name, content, None))
    }
}

#[async_trait]
impl KernelFunction for SemanticFunction {
    fn name(&self) -> &str {
        &self.name
    }
    
    fn description(&self) -> &str {
        &self.description
    }
    
    async fn invoke(&self, kernel: &Kernel, arguments: &HashMap<String, String>) -> crate::Result<String> {
        // Replace variables in the prompt template
        let mut prompt = self.prompt_template.clone();
        for (key, value) in arguments {
            let placeholder = format!("{{{{{}}}}}", key);
            prompt = prompt.replace(&placeholder, value);
        }
        
        // Execute the prompt using the kernel
        kernel.invoke_prompt_async(&prompt).await
    }
}

/// A plugin that wraps a single semantic function
pub struct SemanticFunctionPlugin {
    function: SemanticFunction,
}

impl SemanticFunctionPlugin {
    pub fn new(function: SemanticFunction) -> Self {
        Self { function }
    }
}

#[async_trait]
impl KernelPlugin for SemanticFunctionPlugin {
    fn name(&self) -> &str {
        &self.function.name
    }
    
    fn description(&self) -> &str {
        &self.function.description
    }
    
    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![&self.function]
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_kernel_creation() {
        let kernel = KernelBuilder::new().build();
        assert_eq!(kernel.plugins.len(), 0);
    }

    #[tokio::test]
    async fn test_kernel_invoke_prompt() {
        let kernel = KernelBuilder::new().build();
        let result = kernel.invoke_prompt_async("Hello, world!").await.unwrap();
        assert!(result.contains("Hello, world!"));
    }

    #[tokio::test]
    async fn test_kernel_data() {
        let mut kernel = KernelBuilder::new().build();
        kernel.add_data("test_key", "test_value");
        assert_eq!(kernel.get_data("test_key"), Some(&"test_value".to_string()));
    }

    #[tokio::test]
    async fn test_plugin_namespace_collision() {
        use std::collections::HashMap;
        
        // Create two plugins with the same function name but different implementations
        struct Plugin1;
        struct Plugin2;
        
        struct Function1;
        #[async_trait]
        impl KernelFunction for Function1 {
            fn name(&self) -> &str { "test_function" }
            fn description(&self) -> &str { "Function from plugin 1" }
            async fn invoke(&self, _kernel: &Kernel, _args: &HashMap<String, String>) -> crate::Result<String> {
                Ok("result_from_plugin1".to_string())
            }
        }
        
        struct Function2;
        #[async_trait]
        impl KernelFunction for Function2 {
            fn name(&self) -> &str { "test_function" }
            fn description(&self) -> &str { "Function from plugin 2" }
            async fn invoke(&self, _kernel: &Kernel, _args: &HashMap<String, String>) -> crate::Result<String> {
                Ok("result_from_plugin2".to_string())
            }
        }
        
        #[async_trait]
        impl KernelPlugin for Plugin1 {
            fn name(&self) -> &str { "Plugin1" }
            fn description(&self) -> &str { "First test plugin" }
            fn functions(&self) -> Vec<&dyn KernelFunction> {
                vec![&Function1 as &dyn KernelFunction]
            }
        }
        
        #[async_trait]
        impl KernelPlugin for Plugin2 {
            fn name(&self) -> &str { "Plugin2" }
            fn description(&self) -> &str { "Second test plugin" }
            fn functions(&self) -> Vec<&dyn KernelFunction> {
                vec![&Function2 as &dyn KernelFunction]
            }
        }
        
        // Add both plugins to the kernel
        let kernel = KernelBuilder::new()
            .add_plugin("plugin1", Box::new(Plugin1))
            .add_plugin("plugin2", Box::new(Plugin2))
            .build();
        
        // Verify both plugins are registered with different namespaces
        let plugin1 = kernel.get_plugin("plugin1").unwrap();
        let plugin2 = kernel.get_plugin("plugin2").unwrap();
        
        assert_eq!(plugin1.name(), "Plugin1");
        assert_eq!(plugin2.name(), "Plugin2");
        
        // Verify functions can be called independently through their plugins
        let args = HashMap::new();
        
        let plugin1_functions = plugin1.functions();
        let result1 = plugin1_functions[0].invoke(&kernel, &args).await.unwrap();
        assert_eq!(result1, "result_from_plugin1");
        
        let plugin2_functions = plugin2.functions();
        let result2 = plugin2_functions[0].invoke(&kernel, &args).await.unwrap();
        assert_eq!(result2, "result_from_plugin2");
        
        // Verify both functions have the same name but different results
        assert_eq!(plugin1_functions[0].name(), plugin2_functions[0].name());
        assert_ne!(result1, result2);
    }

    #[tokio::test]
    async fn test_semantic_function_template_substitution() {
        let mut kernel = KernelBuilder::new().build();
        kernel.add_semantic_function("greet", "Hello {{name}}!", Some("Simple greeting".to_string()));
        
        let plugin = kernel.get_plugin("greet").unwrap();
        let functions = plugin.functions();
        let greet_fn = functions.first().unwrap();
        
        let mut args = HashMap::new();
        args.insert("name".to_string(), "World".to_string());
        
        let result = greet_fn.invoke(&kernel, &args).await.unwrap();
        assert!(result.contains("Hello World!"));
    }

    #[tokio::test]
    async fn test_function_json_schema_generation() {
        struct TestFunction;
        
        #[async_trait]
        impl KernelFunction for TestFunction {
            fn name(&self) -> &str { "test_function" }
            fn description(&self) -> &str { "A test function" }
            async fn invoke(&self, _kernel: &Kernel, _args: &HashMap<String, String>) -> crate::Result<String> {
                Ok("test_result".to_string())
            }
        }
        
        let function = TestFunction;
        let schema = function.get_json_schema();
        
        assert_eq!(schema["type"], "function");
        assert_eq!(schema["function"]["name"], "test_function");
        assert_eq!(schema["function"]["description"], "A test function");
        assert_eq!(schema["function"]["parameters"]["type"], "object");
    }
}