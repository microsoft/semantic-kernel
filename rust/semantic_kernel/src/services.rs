//! Service abstractions for AI services and dependency injection

use std::collections::HashMap;
use std::any::{Any, TypeId};
use crate::async_trait;

/// Trait for AI services providing common attributes and metadata
#[async_trait]
pub trait AIService: Send + Sync {
    /// Get the AI service attributes
    fn attributes(&self) -> &HashMap<String, String>;
    
    /// Get service type identifier
    fn service_type(&self) -> &'static str;
}

/// Trait for chat completion services
#[async_trait]
pub trait ChatCompletionService: AIService {
    /// Get chat completion for the given messages
    async fn get_chat_message_content(
        &self,
        messages: &[crate::content::ChatMessage],
        execution_settings: Option<&crate::content::PromptExecutionSettings>,
    ) -> crate::Result<crate::content::ChatMessageContent>;
    
    /// Get streaming chat completion for the given messages
    async fn get_streaming_chat_message_contents(
        &self,
        messages: &[crate::content::ChatMessage],
        execution_settings: Option<&crate::content::PromptExecutionSettings>,
    ) -> crate::Result<Box<dyn futures::Stream<Item = crate::Result<crate::content::StreamingChatMessageContent>> + Send + Unpin>> {
        // Default implementation returns error - services can override
        Err("Streaming not supported by this service".into())
    }
}

/// Trait for text embedding services
#[async_trait]
pub trait EmbeddingService: AIService {
    /// Generate embeddings for the given texts
    async fn generate_embeddings(
        &self,
        texts: &[String],
    ) -> crate::Result<Vec<Vec<f32>>>;
}

/// A simple service provider for dependency injection
pub struct ServiceProvider {
    services: HashMap<TypeId, Box<dyn Any + Send + Sync>>,
    keyed_services: HashMap<String, HashMap<TypeId, Box<dyn Any + Send + Sync>>>,
    chat_completion_service: Option<Box<dyn ChatCompletionService>>,
    embedding_service: Option<Box<dyn EmbeddingService>>,
}

impl ServiceProvider {
    /// Create a new service provider
    pub fn new() -> Self {
        Self {
            services: HashMap::new(),
            keyed_services: HashMap::new(),
            chat_completion_service: None,
            embedding_service: None,
        }
    }

    /// Add a service to the provider
    pub fn add_service<T: 'static + Send + Sync>(&mut self, service: T) {
        self.services.insert(TypeId::of::<T>(), Box::new(service));
    }

    /// Add a keyed service to the provider
    pub fn add_keyed_service<T: 'static + Send + Sync>(&mut self, key: String, service: T) {
        self.keyed_services
            .entry(key)
            .or_default()
            .insert(TypeId::of::<T>(), Box::new(service));
    }

    /// Add a chat completion service
    pub fn add_chat_completion_service<T>(&mut self, service: T)
    where
        T: ChatCompletionService + 'static,
    {
        self.chat_completion_service = Some(Box::new(service));
    }

    /// Add an embedding service
    pub fn add_embedding_service<T>(&mut self, service: T)
    where
        T: EmbeddingService + 'static,
    {
        self.embedding_service = Some(Box::new(service));
    }

    /// Get a service from the provider
    pub fn get_service<T: 'static>(&self) -> Option<&T> {
        self.services
            .get(&TypeId::of::<T>())
            .and_then(|service| service.downcast_ref::<T>())
    }

    /// Get a keyed service from the provider
    pub fn get_keyed_service<T: 'static>(&self, key: &str) -> Option<&T> {
        self.keyed_services
            .get(key)
            .and_then(|services| services.get(&TypeId::of::<T>()))
            .and_then(|service| service.downcast_ref::<T>())
    }

    /// Get the chat completion service
    pub fn get_chat_completion_service(&self) -> Option<&dyn ChatCompletionService> {
        self.chat_completion_service.as_ref().map(|s| s.as_ref())
    }

    /// Get the embedding service
    pub fn get_embedding_service(&self) -> Option<&dyn EmbeddingService> {
        self.embedding_service.as_ref().map(|s| s.as_ref())
    }
}

impl Default for ServiceProvider {
    fn default() -> Self {
        Self::new()
    }
}

/// Builder for the service provider
pub struct ServiceProviderBuilder {
    provider: ServiceProvider,
}

impl ServiceProviderBuilder {
    /// Create a new service provider builder
    pub fn new() -> Self {
        Self {
            provider: ServiceProvider::new(),
        }
    }

    /// Add a service to the builder
    pub fn add_service<T: 'static + Send + Sync>(mut self, service: T) -> Self {
        self.provider.add_service(service);
        self
    }

    /// Add a keyed service to the builder
    pub fn add_keyed_service<T: 'static + Send + Sync>(mut self, key: String, service: T) -> Self {
        self.provider.add_keyed_service(key, service);
        self
    }

    /// Add a chat completion service to the builder
    pub fn add_chat_completion_service<T>(mut self, service: T) -> Self
    where
        T: ChatCompletionService + 'static,
    {
        self.provider.add_chat_completion_service(service);
        self
    }

    /// Add an embedding service to the builder
    pub fn add_embedding_service<T>(mut self, service: T) -> Self
    where
        T: EmbeddingService + 'static,
    {
        self.provider.add_embedding_service(service);
        self
    }

    /// Build the service provider
    pub fn build(self) -> ServiceProvider {
        self.provider
    }
}

impl Default for ServiceProviderBuilder {
    fn default() -> Self {
        Self::new()
    }
}