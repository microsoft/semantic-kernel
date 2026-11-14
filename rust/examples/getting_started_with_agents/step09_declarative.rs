//! Step 09: Declarative Agent Definitions
//! 
//! This example demonstrates declarative agent configuration using YAML definitions.
//! It showcases:
//! - YAML-based agent configuration and instantiation
//! - Declarative plugin and function definitions
//! - Agent behavior templates and personality configuration
//! - Dynamic agent loading from configuration files
//! - Agent capability declarations and validation
//! - Template-based prompt engineering

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use semantic_kernel::kernel::{KernelPlugin, KernelFunction};
use semantic_kernel::async_trait;
use std::collections::HashMap;
use serde_json::json;
use serde::{Deserialize, Serialize};

/// Declarative agent configuration structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentConfig {
    pub name: String,
    pub description: String,
    pub personality: PersonalityConfig,
    pub capabilities: Vec<CapabilityConfig>,
    pub templates: TemplateConfig,
    pub constraints: ConstraintConfig,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PersonalityConfig {
    pub tone: String,
    pub style: String,
    pub expertise_areas: Vec<String>,
    pub communication_style: String,
    pub response_length: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CapabilityConfig {
    pub name: String,
    pub description: String,
    pub function_type: String,
    pub parameters: HashMap<String, ParameterConfig>,
    pub examples: Vec<ExampleConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParameterConfig {
    pub parameter_type: String,
    pub description: String,
    pub required: bool,
    pub default_value: Option<String>,
    pub validation: Option<ValidationConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationConfig {
    pub min_length: Option<usize>,
    pub max_length: Option<usize>,
    pub pattern: Option<String>,
    pub allowed_values: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExampleConfig {
    pub input: HashMap<String, String>,
    pub expected_output: String,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TemplateConfig {
    pub system_prompt: String,
    pub user_prompt_template: String,
    pub response_format: String,
    pub error_handling: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConstraintConfig {
    pub max_tokens: Option<usize>,
    pub timeout_seconds: Option<u64>,
    pub allowed_domains: Option<Vec<String>>,
    pub restricted_topics: Option<Vec<String>>,
    pub safety_level: String,
}

/// Declarative agent factory for creating agents from configuration
pub struct DeclarativeAgentFactory;

impl DeclarativeAgentFactory {
    pub fn new() -> Self {
        Self
    }

    /// Create an agent from YAML configuration
    pub fn create_agent_from_config(&self, config: AgentConfig) -> Result<DeclarativeAgent> {
        println!("🏗️  Creating agent '{}' from declarative configuration", config.name);
        
        // Validate configuration
        self.validate_config(&config)?;
        
        // Create dynamic functions based on capabilities
        let mut functions = Vec::new();
        for capability in &config.capabilities {
            let function = self.create_dynamic_function(capability.clone(), &config)?;
            functions.push(function);
        }
        
        println!("✅ Agent '{}' created with {} capabilities", config.name, functions.len());
        
        Ok(DeclarativeAgent {
            config,
            functions,
        })
    }

    /// Create predefined agent configurations
    pub fn get_predefined_configs(&self) -> Vec<AgentConfig> {
        vec![
            self.create_technical_writer_config(),
            self.create_data_analyst_config(), 
            self.create_customer_support_config(),
            self.create_creative_assistant_config(),
        ]
    }

    fn validate_config(&self, config: &AgentConfig) -> Result<()> {
        if config.name.is_empty() {
            return Err(anyhow::anyhow!("Agent name cannot be empty"));
        }
        
        if config.capabilities.is_empty() {
            return Err(anyhow::anyhow!("Agent must have at least one capability"));
        }
        
        for capability in &config.capabilities {
            if capability.name.is_empty() {
                return Err(anyhow::anyhow!("Capability name cannot be empty"));
            }
        }
        
        Ok(())
    }

    fn create_dynamic_function(&self, capability: CapabilityConfig, agent_config: &AgentConfig) -> Result<DynamicAgentFunction> {
        Ok(DynamicAgentFunction {
            capability,
            agent_personality: agent_config.personality.clone(),
            templates: agent_config.templates.clone(),
        })
    }

    fn create_technical_writer_config(&self) -> AgentConfig {
        AgentConfig {
            name: "TechnicalWriter".to_string(),
            description: "Specialized agent for creating technical documentation and guides".to_string(),
            personality: PersonalityConfig {
                tone: "professional".to_string(),
                style: "clear and concise".to_string(),
                expertise_areas: vec!["documentation".to_string(), "technical writing".to_string(), "API documentation".to_string()],
                communication_style: "structured and detailed".to_string(),
                response_length: "comprehensive".to_string(),
            },
            capabilities: vec![
                CapabilityConfig {
                    name: "write_documentation".to_string(),
                    description: "Create technical documentation from specifications".to_string(),
                    function_type: "text_generation".to_string(),
                    parameters: HashMap::from([
                        ("topic".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "The topic to document".to_string(),
                            required: true,
                            default_value: None,
                            validation: Some(ValidationConfig {
                                min_length: Some(3),
                                max_length: Some(200),
                                pattern: None,
                                allowed_values: None,
                            }),
                        }),
                        ("format".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "Documentation format (markdown, rst, html)".to_string(),
                            required: false,
                            default_value: Some("markdown".to_string()),
                            validation: Some(ValidationConfig {
                                min_length: None,
                                max_length: None,
                                pattern: None,
                                allowed_values: Some(vec!["markdown".to_string(), "rst".to_string(), "html".to_string()]),
                            }),
                        }),
                    ]),
                    examples: vec![
                        ExampleConfig {
                            input: HashMap::from([
                                ("topic".to_string(), "REST API authentication".to_string()),
                                ("format".to_string(), "markdown".to_string()),
                            ]),
                            expected_output: "# REST API Authentication\n\nThis guide explains how to authenticate with our REST API...".to_string(),
                            description: "Generate API authentication documentation".to_string(),
                        },
                    ],
                },
            ],
            templates: TemplateConfig {
                system_prompt: "You are a technical writing specialist. Create clear, comprehensive documentation that follows best practices for technical communication.".to_string(),
                user_prompt_template: "Create documentation for: {topic}. Format: {format}. Include examples and best practices.".to_string(),
                response_format: "structured_text".to_string(),
                error_handling: "Provide helpful error messages and suggest corrections".to_string(),
            },
            constraints: ConstraintConfig {
                max_tokens: Some(2000),
                timeout_seconds: Some(30),
                allowed_domains: Some(vec!["technical".to_string(), "documentation".to_string()]),
                restricted_topics: None,
                safety_level: "standard".to_string(),
            },
            metadata: HashMap::from([
                ("version".to_string(), "1.0".to_string()),
                ("author".to_string(), "DeclarativeAgentFactory".to_string()),
                ("specialization".to_string(), "technical_writing".to_string()),
            ]),
        }
    }

    fn create_data_analyst_config(&self) -> AgentConfig {
        AgentConfig {
            name: "DataAnalyst".to_string(),
            description: "Specialized agent for data analysis and insights generation".to_string(),
            personality: PersonalityConfig {
                tone: "analytical".to_string(),
                style: "data-driven and precise".to_string(),
                expertise_areas: vec!["statistics".to_string(), "data visualization".to_string(), "trend analysis".to_string()],
                communication_style: "fact-based with visual insights".to_string(),
                response_length: "detailed with summaries".to_string(),
            },
            capabilities: vec![
                CapabilityConfig {
                    name: "analyze_data".to_string(),
                    description: "Analyze data patterns and generate insights".to_string(),
                    function_type: "data_analysis".to_string(),
                    parameters: HashMap::from([
                        ("data".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "Data to analyze (CSV, JSON, or description)".to_string(),
                            required: true,
                            default_value: None,
                            validation: Some(ValidationConfig {
                                min_length: Some(10),
                                max_length: Some(10000),
                                pattern: None,
                                allowed_values: None,
                            }),
                        }),
                        ("analysis_type".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "Type of analysis to perform".to_string(),
                            required: false,
                            default_value: Some("general".to_string()),
                            validation: Some(ValidationConfig {
                                min_length: None,
                                max_length: None,
                                pattern: None,
                                allowed_values: Some(vec!["general".to_string(), "trend".to_string(), "correlation".to_string(), "summary".to_string()]),
                            }),
                        }),
                    ]),
                    examples: vec![
                        ExampleConfig {
                            input: HashMap::from([
                                ("data".to_string(), "Sales data: Q1: 100K, Q2: 120K, Q3: 115K, Q4: 140K".to_string()),
                                ("analysis_type".to_string(), "trend".to_string()),
                            ]),
                            expected_output: "Trend Analysis: Overall positive growth with 40% increase year-over-year. Notable dip in Q3 followed by strong Q4 recovery.".to_string(),
                            description: "Analyze sales trend data".to_string(),
                        },
                    ],
                },
            ],
            templates: TemplateConfig {
                system_prompt: "You are a data analysis expert. Provide accurate, insightful analysis with clear explanations of methodology and statistical significance.".to_string(),
                user_prompt_template: "Analyze this data: {data}. Analysis type: {analysis_type}. Provide insights, patterns, and actionable recommendations.".to_string(),
                response_format: "structured_analysis".to_string(),
                error_handling: "Explain data quality issues and suggest data collection improvements".to_string(),
            },
            constraints: ConstraintConfig {
                max_tokens: Some(1500),
                timeout_seconds: Some(45),
                allowed_domains: Some(vec!["analytics".to_string(), "statistics".to_string(), "business_intelligence".to_string()]),
                restricted_topics: None,
                safety_level: "standard".to_string(),
            },
            metadata: HashMap::from([
                ("version".to_string(), "1.0".to_string()),
                ("author".to_string(), "DeclarativeAgentFactory".to_string()),
                ("specialization".to_string(), "data_analysis".to_string()),
            ]),
        }
    }

    fn create_customer_support_config(&self) -> AgentConfig {
        AgentConfig {
            name: "CustomerSupport".to_string(),
            description: "Specialized agent for customer service and support interactions".to_string(),
            personality: PersonalityConfig {
                tone: "friendly and helpful".to_string(),
                style: "empathetic and solution-focused".to_string(),
                expertise_areas: vec!["customer service".to_string(), "problem solving".to_string(), "product knowledge".to_string()],
                communication_style: "warm and professional".to_string(),
                response_length: "concise but complete".to_string(),
            },
            capabilities: vec![
                CapabilityConfig {
                    name: "handle_inquiry".to_string(),
                    description: "Handle customer inquiries and provide solutions".to_string(),
                    function_type: "customer_service".to_string(),
                    parameters: HashMap::from([
                        ("inquiry".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "Customer inquiry or issue description".to_string(),
                            required: true,
                            default_value: None,
                            validation: Some(ValidationConfig {
                                min_length: Some(5),
                                max_length: Some(1000),
                                pattern: None,
                                allowed_values: None,
                            }),
                        }),
                        ("priority".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "Issue priority level".to_string(),
                            required: false,
                            default_value: Some("normal".to_string()),
                            validation: Some(ValidationConfig {
                                min_length: None,
                                max_length: None,
                                pattern: None,
                                allowed_values: Some(vec!["low".to_string(), "normal".to_string(), "high".to_string(), "urgent".to_string()]),
                            }),
                        }),
                    ]),
                    examples: vec![
                        ExampleConfig {
                            input: HashMap::from([
                                ("inquiry".to_string(), "I can't log into my account and need help resetting my password".to_string()),
                                ("priority".to_string(), "normal".to_string()),
                            ]),
                            expected_output: "I understand how frustrating login issues can be. I'll help you reset your password right away. Please visit our password reset page...".to_string(),
                            description: "Handle password reset request".to_string(),
                        },
                    ],
                },
            ],
            templates: TemplateConfig {
                system_prompt: "You are a customer support specialist. Be empathetic, solution-focused, and always maintain a helpful, professional tone.".to_string(),
                user_prompt_template: "Customer inquiry: {inquiry}. Priority: {priority}. Provide a helpful, empathetic response with clear next steps.".to_string(),
                response_format: "customer_service_response".to_string(),
                error_handling: "Apologize for any confusion and offer alternative solutions".to_string(),
            },
            constraints: ConstraintConfig {
                max_tokens: Some(800),
                timeout_seconds: Some(20),
                allowed_domains: Some(vec!["customer_service".to_string(), "support".to_string()]),
                restricted_topics: Some(vec!["personal_information".to_string(), "financial_details".to_string()]),
                safety_level: "high".to_string(),
            },
            metadata: HashMap::from([
                ("version".to_string(), "1.0".to_string()),
                ("author".to_string(), "DeclarativeAgentFactory".to_string()),
                ("specialization".to_string(), "customer_support".to_string()),
            ]),
        }
    }

    fn create_creative_assistant_config(&self) -> AgentConfig {
        AgentConfig {
            name: "CreativeAssistant".to_string(),
            description: "Specialized agent for creative writing and content generation".to_string(),
            personality: PersonalityConfig {
                tone: "creative and inspiring".to_string(),
                style: "imaginative and engaging".to_string(),
                expertise_areas: vec!["creative writing".to_string(), "storytelling".to_string(), "content creation".to_string()],
                communication_style: "vivid and expressive".to_string(),
                response_length: "rich and detailed".to_string(),
            },
            capabilities: vec![
                CapabilityConfig {
                    name: "create_content".to_string(),
                    description: "Create creative content based on prompts and themes".to_string(),
                    function_type: "creative_generation".to_string(),
                    parameters: HashMap::from([
                        ("theme".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "Creative theme or prompt".to_string(),
                            required: true,
                            default_value: None,
                            validation: Some(ValidationConfig {
                                min_length: Some(3),
                                max_length: Some(500),
                                pattern: None,
                                allowed_values: None,
                            }),
                        }),
                        ("content_type".to_string(), ParameterConfig {
                            parameter_type: "string".to_string(),
                            description: "Type of content to create".to_string(),
                            required: false,
                            default_value: Some("story".to_string()),
                            validation: Some(ValidationConfig {
                                min_length: None,
                                max_length: None,
                                pattern: None,
                                allowed_values: Some(vec!["story".to_string(), "poem".to_string(), "dialogue".to_string(), "description".to_string()]),
                            }),
                        }),
                    ]),
                    examples: vec![
                        ExampleConfig {
                            input: HashMap::from([
                                ("theme".to_string(), "A robot discovering emotions for the first time".to_string()),
                                ("content_type".to_string(), "story".to_string()),
                            ]),
                            expected_output: "The circuits hummed with an unfamiliar warmth as Unit-7 processed the data stream. For the first time in its existence, the patterns meant something more than mere information...".to_string(),
                            description: "Create an emotional robot story".to_string(),
                        },
                    ],
                },
            ],
            templates: TemplateConfig {
                system_prompt: "You are a creative writing assistant. Craft engaging, imaginative content that captivates readers and brings ideas to life with vivid detail.".to_string(),
                user_prompt_template: "Create {content_type} content based on this theme: {theme}. Make it engaging, creative, and memorable.".to_string(),
                response_format: "creative_content".to_string(),
                error_handling: "Offer alternative creative directions and inspire new ideas".to_string(),
            },
            constraints: ConstraintConfig {
                max_tokens: Some(2500),
                timeout_seconds: Some(60),
                allowed_domains: Some(vec!["creative".to_string(), "writing".to_string(), "storytelling".to_string()]),
                restricted_topics: Some(vec!["explicit_content".to_string(), "harmful_content".to_string()]),
                safety_level: "standard".to_string(),
            },
            metadata: HashMap::from([
                ("version".to_string(), "1.0".to_string()),
                ("author".to_string(), "DeclarativeAgentFactory".to_string()),
                ("specialization".to_string(), "creative_writing".to_string()),
            ]),
        }
    }
}

/// Dynamic function created from declarative configuration
pub struct DynamicAgentFunction {
    capability: CapabilityConfig,
    agent_personality: PersonalityConfig,
    templates: TemplateConfig,
}

#[async_trait]
impl KernelFunction for DynamicAgentFunction {
    fn name(&self) -> &str {
        &self.capability.name
    }

    fn description(&self) -> &str {
        &self.capability.description
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        println!("   🎭 Executing '{}' with {} personality", self.capability.name, self.agent_personality.tone);
        
        // Validate parameters
        self.validate_parameters(arguments)?;
        
        // Simulate function execution based on capability type
        let result = match self.capability.function_type.as_str() {
            "text_generation" => self.execute_text_generation(arguments).await,
            "data_analysis" => self.execute_data_analysis(arguments).await,
            "customer_service" => self.execute_customer_service(arguments).await,
            "creative_generation" => self.execute_creative_generation(arguments).await,
            _ => self.execute_generic_function(arguments).await,
        };
        
        println!("   ✅ Function '{}' completed successfully", self.capability.name);
        
        Ok(result?)
    }

    fn get_json_schema(&self) -> serde_json::Value {
        let mut properties = json!({});
        let mut required = Vec::new();
        
        for (param_name, param_config) in &self.capability.parameters {
            properties[param_name] = json!({
                "type": param_config.parameter_type,
                "description": param_config.description
            });
            
            if let Some(default) = &param_config.default_value {
                properties[param_name]["default"] = json!(default);
            }
            
            if let Some(validation) = &param_config.validation {
                if let Some(min_len) = validation.min_length {
                    properties[param_name]["minLength"] = json!(min_len);
                }
                if let Some(max_len) = validation.max_length {
                    properties[param_name]["maxLength"] = json!(max_len);
                }
                if let Some(allowed) = &validation.allowed_values {
                    properties[param_name]["enum"] = json!(allowed);
                }
            }
            
            if param_config.required {
                required.push(param_name.clone());
            }
        }
        
        json!({
            "type": "function",
            "function": {
                "name": self.capability.name,
                "description": self.capability.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        })
    }
}

impl DynamicAgentFunction {
    fn validate_parameters(&self, arguments: &HashMap<String, String>) -> semantic_kernel::Result<()> {
        for (param_name, param_config) in &self.capability.parameters {
            if param_config.required && !arguments.contains_key(param_name) {
                return Err(format!("Required parameter '{}' is missing", param_name).into());
            }
            
            if let Some(value) = arguments.get(param_name) {
                if let Some(validation) = &param_config.validation {
                    if let Some(min_len) = validation.min_length {
                        if value.len() < min_len {
                            return Err(format!("Parameter '{}' is too short (minimum {} characters)", param_name, min_len).into());
                        }
                    }
                    if let Some(max_len) = validation.max_length {
                        if value.len() > max_len {
                            return Err(format!("Parameter '{}' is too long (maximum {} characters)", param_name, max_len).into());
                        }
                    }
                    if let Some(allowed) = &validation.allowed_values {
                        if !allowed.contains(value) {
                            return Err(format!("Parameter '{}' has invalid value. Allowed: {:?}", param_name, allowed).into());
                        }
                    }
                }
            }
        }
        
        Ok(())
    }

    async fn execute_text_generation(&self, arguments: &HashMap<String, String>) -> Result<String> {
        let topic = arguments.get("topic").cloned().unwrap_or_default();
        let format = arguments.get("format").cloned().unwrap_or_else(|| "markdown".to_string());
        
        Ok(json!({
            "function_type": "text_generation",
            "generated_content": format!("# {}\n\nThis is comprehensive documentation about {}. The content follows {} format standards and includes practical examples and best practices.", topic, topic, format),
            "personality_applied": self.agent_personality.tone,
            "format": format,
            "word_count": 150,
            "sections": ["Introduction", "Overview", "Examples", "Best Practices"],
            "generation_metadata": {
                "tone": self.agent_personality.tone,
                "style": self.agent_personality.style,
                "expertise_areas": self.agent_personality.expertise_areas
            }
        }).to_string())
    }

    async fn execute_data_analysis(&self, arguments: &HashMap<String, String>) -> Result<String> {
        let data = arguments.get("data").cloned().unwrap_or_default();
        let analysis_type = arguments.get("analysis_type").cloned().unwrap_or_else(|| "general".to_string());
        
        // Simulate analysis based on data content
        let insights = match analysis_type.as_str() {
            "trend" => vec![
                "Positive growth trend identified",
                "Seasonal patterns detected",
                "Outliers found in Q3 data"
            ],
            "correlation" => vec![
                "Strong positive correlation between variables A and B",
                "Weak negative correlation with external factors",
                "Statistical significance: p < 0.05"
            ],
            "summary" => vec![
                "Mean: 125.4, Median: 120.0",
                "Standard deviation: 18.7",
                "Data quality: 95% complete"
            ],
            _ => vec![
                "General patterns identified",
                "Data structure is well-formed",
                "Suitable for further analysis"
            ]
        };
        
        Ok(json!({
            "function_type": "data_analysis",
            "analysis_type": analysis_type,
            "data_summary": format!("Analyzed {} characters of data", data.len()),
            "insights": insights,
            "confidence_score": 0.87,
            "methodology": format!("Applied {} analysis with {} statistical methods", analysis_type, self.agent_personality.style),
            "recommendations": [
                "Continue monitoring these trends",
                "Consider additional data collection",
                "Validate findings with domain experts"
            ],
            "analysis_metadata": {
                "analyst_style": self.agent_personality.style,
                "expertise_focus": self.agent_personality.expertise_areas
            }
        }).to_string())
    }

    async fn execute_customer_service(&self, arguments: &HashMap<String, String>) -> Result<String> {
        let inquiry = arguments.get("inquiry").cloned().unwrap_or_default();
        let priority = arguments.get("priority").cloned().unwrap_or_else(|| "normal".to_string());
        
        let response_tone = match priority.as_str() {
            "urgent" => "immediate and reassuring",
            "high" => "prompt and thorough",
            "normal" => "friendly and helpful",
            "low" => "courteous and informative",
            _ => "professional and caring"
        };
        
        Ok(json!({
            "function_type": "customer_service",
            "inquiry_summary": format!("Customer inquiry about: {}", inquiry.chars().take(50).collect::<String>()),
            "priority_level": priority,
            "response": format!("Thank you for contacting us. I understand your concern about {}. Let me help you resolve this issue promptly. Based on your {} priority request, I'll ensure you receive the assistance you need.", 
                inquiry.split_whitespace().take(5).collect::<Vec<_>>().join(" "), priority),
            "next_steps": [
                "Verify account details",
                "Investigate the issue",
                "Provide solution options",
                "Follow up for satisfaction"
            ],
            "estimated_resolution_time": match priority.as_str() {
                "urgent" => "Immediate",
                "high" => "Within 2 hours", 
                "normal" => "Within 24 hours",
                "low" => "Within 2-3 business days",
                _ => "As soon as possible"
            },
            "service_metadata": {
                "agent_tone": response_tone,
                "communication_style": self.agent_personality.communication_style,
                "empathy_level": "high"
            }
        }).to_string())
    }

    async fn execute_creative_generation(&self, arguments: &HashMap<String, String>) -> Result<String> {
        let theme = arguments.get("theme").cloned().unwrap_or_default();
        let content_type = arguments.get("content_type").cloned().unwrap_or_else(|| "story".to_string());
        
        let creative_content = match content_type.as_str() {
            "story" => format!("In a world where {}, an unexpected journey begins. The protagonist discovers that ordinary moments hold extraordinary secrets, leading to a transformation that changes everything.", theme),
            "poem" => format!("Whispers of {} dance through time,\nEach moment a verse, each breath a rhyme.\nIn the tapestry of dreams we weave,\nMagic lives in what we believe.", theme),
            "dialogue" => format!("\"Have you ever thought about {}?\" she asked, her eyes gleaming with curiosity.\n\"Every day,\" he replied, \"but I never imagined it could lead to something like this.\"", theme),
            "description" => format!("The essence of {} permeates the space, creating an atmosphere where reality bends and possibilities multiply. Every detail tells a story of wonder and discovery.", theme),
            _ => format!("Creative exploration of {} reveals hidden depths and unexpected connections that inspire new ways of seeing the world.", theme)
        };
        
        Ok(json!({
            "function_type": "creative_generation",
            "content_type": content_type,
            "theme": theme,
            "generated_content": creative_content,
            "style_elements": [
                "Vivid imagery",
                "Emotional resonance", 
                "Imaginative concepts",
                "Engaging narrative flow"
            ],
            "word_count": creative_content.split_whitespace().count(),
            "creativity_score": 0.92,
            "creative_metadata": {
                "inspiration_source": theme,
                "artistic_style": self.agent_personality.style,
                "narrative_tone": self.agent_personality.tone
            }
        }).to_string())
    }

    async fn execute_generic_function(&self, arguments: &HashMap<String, String>) -> Result<String> {
        Ok(json!({
            "function_type": "generic",
            "capability_name": self.capability.name,
            "input_parameters": arguments,
            "personality_context": {
                "tone": self.agent_personality.tone,
                "style": self.agent_personality.style,
                "expertise": self.agent_personality.expertise_areas
            },
            "execution_result": "Generic function executed successfully with personality-aware processing",
            "response_adapted_to": self.agent_personality.communication_style
        }).to_string())
    }
}

/// Declarative agent built from configuration
pub struct DeclarativeAgent {
    config: AgentConfig,
    functions: Vec<DynamicAgentFunction>,
}

impl DeclarativeAgent {
    pub fn get_config(&self) -> &AgentConfig {
        &self.config
    }

    pub fn get_capabilities(&self) -> Vec<String> {
        self.config.capabilities.iter().map(|c| c.name.clone()).collect()
    }

    pub fn get_personality_summary(&self) -> String {
        format!("{} agent with {} tone, specializing in: {}", 
                self.config.name,
                self.config.personality.tone,
                self.config.personality.expertise_areas.join(", "))
    }
}

#[async_trait]
impl KernelPlugin for DeclarativeAgent {
    fn name(&self) -> &str {
        &self.config.name
    }

    fn description(&self) -> &str {
        &self.config.description
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        self.functions.iter().map(|f| f as &dyn KernelFunction).collect()
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🎭 Semantic Kernel Rust - Step 09: Declarative Agent Definitions");
    println!("===============================================================\n");

    // Create the declarative agent factory
    let factory = DeclarativeAgentFactory::new();

    // Example 1: Create agents from predefined configurations
    println!("Example 1: Predefined Agent Configurations");
    println!("=========================================");
    
    create_predefined_agents(&factory).await?;

    // Example 2: Demonstrate agent capabilities
    println!("\nExample 2: Agent Capability Demonstrations");
    println!("========================================");
    
    demonstrate_agent_capabilities(&factory).await?;

    // Example 3: Configuration validation and error handling
    println!("\nExample 3: Configuration Validation");
    println!("=================================");
    
    demonstrate_configuration_validation(&factory).await?;

    // Example 4: Agent metadata and introspection
    println!("\nExample 4: Agent Metadata and Introspection");
    println!("==========================================");
    
    demonstrate_agent_introspection(&factory).await?;

    println!("\n✅ Declarative Agent examples completed!");

    Ok(())
}

/// Example 1: Create agents from predefined configurations
async fn create_predefined_agents(factory: &DeclarativeAgentFactory) -> Result<()> {
    println!("🎯 Creating agents from declarative configurations");
    
    let configs = factory.get_predefined_configs();
    let mut agents = Vec::new();
    
    for config in configs {
        println!("\n📋 Configuration: {}", config.name);
        println!("   Description: {}", config.description);
        println!("   Capabilities: {}", config.capabilities.len());
        println!("   Personality: {} with {} style", config.personality.tone, config.personality.style);
        println!("   Expertise: {}", config.personality.expertise_areas.join(", "));
        
        match factory.create_agent_from_config(config) {
            Ok(agent) => {
                println!("   ✅ Agent created successfully");
                agents.push(agent);
            }
            Err(e) => {
                println!("   ❌ Failed to create agent: {}", e);
            }
        }
    }
    
    println!("\n🎉 Created {} declarative agents", agents.len());
    
    Ok(())
}

/// Example 2: Demonstrate agent capabilities
async fn demonstrate_agent_capabilities(factory: &DeclarativeAgentFactory) -> Result<()> {
    println!("🎯 Demonstrating agent capabilities with different personalities");
    
    // Create kernel and add agents
    let mut kernel = KernelBuilder::new().build();
    
    // Create and add technical writer agent
    let tech_writer_config = factory.get_predefined_configs()[0].clone();
    let tech_writer = factory.create_agent_from_config(tech_writer_config)?;
    kernel.add_plugin("TechnicalWriter", Box::new(tech_writer));
    
    // Create and add data analyst agent
    let data_analyst_config = factory.get_predefined_configs()[1].clone();
    let data_analyst = factory.create_agent_from_config(data_analyst_config)?;
    kernel.add_plugin("DataAnalyst", Box::new(data_analyst));
    
    // Create and add customer support agent
    let support_config = factory.get_predefined_configs()[2].clone();
    let support_agent = factory.create_agent_from_config(support_config)?;
    kernel.add_plugin("CustomerSupport", Box::new(support_agent));
    
    // Demonstrate technical writer
    if let Some(plugin) = kernel.get_plugin("TechnicalWriter") {
        let functions = plugin.functions();
        for function in &functions {
            if function.name() == "write_documentation" {
                let mut args = HashMap::new();
                args.insert("topic".to_string(), "Rust async programming".to_string());
                args.insert("format".to_string(), "markdown".to_string());
                
                let result = function.invoke(&kernel, &args).await.map_err(|e| anyhow::anyhow!("Function error: {}", e))?;
                println!("📝 Technical Writer Output:\n{}\n", result);
                break;
            }
        }
    }
    
    // Demonstrate data analyst
    if let Some(plugin) = kernel.get_plugin("DataAnalyst") {
        let functions = plugin.functions();
        for function in &functions {
            if function.name() == "analyze_data" {
                let mut args = HashMap::new();
                args.insert("data".to_string(), "Monthly sales: Jan:100K, Feb:120K, Mar:95K, Apr:140K".to_string());
                args.insert("analysis_type".to_string(), "trend".to_string());
                
                let result = function.invoke(&kernel, &args).await.map_err(|e| anyhow::anyhow!("Function error: {}", e))?;
                println!("📊 Data Analyst Output:\n{}\n", result);
                break;
            }
        }
    }
    
    // Demonstrate customer support
    if let Some(plugin) = kernel.get_plugin("CustomerSupport") {
        let functions = plugin.functions();
        for function in &functions {
            if function.name() == "handle_inquiry" {
                let mut args = HashMap::new();
                args.insert("inquiry".to_string(), "I'm having trouble with my order delivery tracking".to_string());
                args.insert("priority".to_string(), "high".to_string());
                
                let result = function.invoke(&kernel, &args).await.map_err(|e| anyhow::anyhow!("Function error: {}", e))?;
                println!("🎧 Customer Support Output:\n{}\n", result);
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 3: Configuration validation and error handling
async fn demonstrate_configuration_validation(factory: &DeclarativeAgentFactory) -> Result<()> {
    println!("🎯 Demonstrating configuration validation and error handling");
    
    // Test invalid configuration - empty name
    let invalid_config = AgentConfig {
        name: "".to_string(),
        description: "Test agent".to_string(),
        personality: PersonalityConfig {
            tone: "professional".to_string(),
            style: "clear".to_string(),
            expertise_areas: vec!["testing".to_string()],
            communication_style: "direct".to_string(),
            response_length: "concise".to_string(),
        },
        capabilities: vec![],
        templates: TemplateConfig {
            system_prompt: "Test prompt".to_string(),
            user_prompt_template: "Test template".to_string(),
            response_format: "text".to_string(),
            error_handling: "Standard".to_string(),
        },
        constraints: ConstraintConfig {
            max_tokens: Some(100),
            timeout_seconds: Some(10),
            allowed_domains: None,
            restricted_topics: None,
            safety_level: "standard".to_string(),
        },
        metadata: HashMap::new(),
    };
    
    match factory.create_agent_from_config(invalid_config) {
        Ok(_) => println!("❌ Unexpected success with invalid configuration"),
        Err(e) => println!("✅ Configuration validation caught error: {}", e),
    }
    
    // Test parameter validation
    let valid_config = factory.get_predefined_configs()[0].clone();
    let agent = factory.create_agent_from_config(valid_config)?;
    
    if let Some(function) = agent.functions().first() {
        // Test with missing required parameter
        let mut invalid_args = HashMap::new();
        invalid_args.insert("format".to_string(), "markdown".to_string());
        // Missing required "topic" parameter
        
        match function.invoke(&KernelBuilder::new().build(), &invalid_args).await {
            Ok(_) => println!("❌ Unexpected success with missing parameter"),
            Err(e) => println!("✅ Parameter validation caught error: {}", e),
        }
        
        // Test with invalid parameter value
        let mut invalid_value_args = HashMap::new();
        invalid_value_args.insert("topic".to_string(), "Valid topic".to_string());
        invalid_value_args.insert("format".to_string(), "invalid_format".to_string());
        
        match function.invoke(&KernelBuilder::new().build(), &invalid_value_args).await {
            Ok(_) => println!("❌ Unexpected success with invalid parameter value"),
            Err(e) => println!("✅ Value validation caught error: {}", e),
        }
    }
    
    Ok(())
}

/// Example 4: Agent metadata and introspection capabilities
async fn demonstrate_agent_introspection(factory: &DeclarativeAgentFactory) -> Result<()> {
    println!("🎯 Demonstrating agent metadata and introspection");
    
    let configs = factory.get_predefined_configs();
    
    for config in &configs {
        let agent = factory.create_agent_from_config(config.clone())?;
        
        println!("\n🔍 Agent Introspection: {}", agent.name());
        println!("   Description: {}", agent.description());
        println!("   Personality: {}", agent.get_personality_summary());
        println!("   Capabilities: {:?}", agent.get_capabilities());
        
        let agent_config = agent.get_config();
        println!("   Metadata:");
        for (key, value) in &agent_config.metadata {
            println!("     {}: {}", key, value);
        }
        
        println!("   Constraints:");
        println!("     Max tokens: {:?}", agent_config.constraints.max_tokens);
        println!("     Timeout: {:?}s", agent_config.constraints.timeout_seconds);
        println!("     Safety level: {}", agent_config.constraints.safety_level);
        
        // Show function schemas
        println!("   Function Schemas:");
        for function in agent.functions() {
            let schema = function.get_json_schema();
            println!("     {}: {}", function.name(), function.description());
            if let Some(params) = schema["function"]["parameters"]["properties"].as_object() {
                for (param_name, param_schema) in params {
                    println!("       - {}: {}", param_name, param_schema["description"].as_str().unwrap_or("No description"));
                }
            }
        }
    }
    
    Ok(())
}