//! Step 01: Basic Text Search Operations
//! 
//! This example demonstrates fundamental text search operations using the Semantic Kernel.
//! It showcases:
//! - Basic text matching and filtering
//! - Pattern-based search with regex support
//! - Full-text search with scoring
//! - Multi-criteria search combinations
//! - Search result ranking and relevance scoring
//! - Text preprocessing and normalization

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use semantic_kernel::kernel::{KernelPlugin, KernelFunction};
use semantic_kernel::async_trait;
use std::collections::HashMap;
use serde_json::json;
use regex::Regex;

/// Document structure for text search operations
#[derive(Debug, Clone)]
pub struct TextDocument {
    pub id: String,
    pub title: String,
    pub content: String,
    pub tags: Vec<String>,
    pub category: String,
    pub word_count: usize,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

impl TextDocument {
    pub fn new(id: String, title: String, content: String, category: String, tags: Vec<String>) -> Self {
        let word_count = content.split_whitespace().count();
        Self {
            id,
            title,
            content,
            tags,
            category,
            word_count,
            created_at: chrono::Utc::now(),
        }
    }

    /// Calculate relevance score for a query
    pub fn relevance_score(&self, query: &str) -> f64 {
        let query_lower = query.to_lowercase();
        let title_lower = self.title.to_lowercase();
        let content_lower = self.content.to_lowercase();
        
        let mut score = 0.0;
        
        // Title match (high weight)
        if title_lower.contains(&query_lower) {
            score += 10.0;
        }
        
        // Content match (medium weight)
        let content_matches = content_lower.matches(&query_lower).count() as f64;
        score += content_matches * 2.0;
        
        // Tag match (high weight)
        for tag in &self.tags {
            if tag.to_lowercase().contains(&query_lower) {
                score += 8.0;
            }
        }
        
        // Category match (medium weight)
        if self.category.to_lowercase().contains(&query_lower) {
            score += 5.0;
        }
        
        // Normalize by document length (shorter documents with matches score higher)
        if score > 0.0 && self.word_count > 0 {
            score = score * (1000.0 / (self.word_count as f64).max(100.0));
        }
        
        score
    }
}

/// Text search plugin providing various search capabilities
pub struct TextSearchPlugin {
    documents: Vec<TextDocument>,
    basic_search: BasicSearchFunction,
    regex_search: RegexSearchFunction,
    category_search: CategorySearchFunction,
    tag_search: TagSearchFunction,
    ranked_search: RankedSearchFunction,
}

impl TextSearchPlugin {
    pub fn new() -> Self {
        // Create sample documents for demonstration
        let documents = vec![
            TextDocument::new(
                "doc1".to_string(),
                "Rust Programming Fundamentals".to_string(),
                "Rust is a systems programming language that focuses on safety, speed, and concurrency. It achieves memory safety without garbage collection through its ownership system.".to_string(),
                "Programming".to_string(),
                vec!["rust".to_string(), "systems".to_string(), "memory-safety".to_string()]
            ),
            TextDocument::new(
                "doc2".to_string(),
                "Machine Learning with Python".to_string(),
                "Python is widely used for machine learning due to its extensive libraries like scikit-learn, TensorFlow, and PyTorch. These tools make it easy to build and deploy ML models.".to_string(),
                "Data Science".to_string(),
                vec!["python".to_string(), "ml".to_string(), "tensorflow".to_string(), "pytorch".to_string()]
            ),
            TextDocument::new(
                "doc3".to_string(),
                "Web Development Best Practices".to_string(),
                "Modern web development involves using frameworks like React, Vue, or Angular for frontend, and Node.js, Django, or Ruby on Rails for backend development.".to_string(),
                "Web Development".to_string(),
                vec!["web".to_string(), "react".to_string(), "nodejs".to_string(), "django".to_string()]
            ),
            TextDocument::new(
                "doc4".to_string(),
                "Database Design Principles".to_string(),
                "Effective database design requires understanding normalization, indexing, and query optimization. SQL databases like PostgreSQL and MySQL are commonly used for structured data.".to_string(),
                "Database".to_string(),
                vec!["database".to_string(), "sql".to_string(), "postgresql".to_string(), "optimization".to_string()]
            ),
            TextDocument::new(
                "doc5".to_string(),
                "Cloud Computing Architecture".to_string(),
                "Cloud platforms like AWS, Azure, and Google Cloud provide scalable infrastructure for modern applications. Microservices and containerization with Docker and Kubernetes are key patterns.".to_string(),
                "Cloud".to_string(),
                vec!["cloud".to_string(), "aws".to_string(), "azure".to_string(), "kubernetes".to_string(), "docker".to_string()]
            ),
        ];
        
        Self {
            basic_search: BasicSearchFunction { documents: documents.clone() },
            regex_search: RegexSearchFunction { documents: documents.clone() },
            category_search: CategorySearchFunction { documents: documents.clone() },
            tag_search: TagSearchFunction { documents: documents.clone() },
            ranked_search: RankedSearchFunction { documents: documents.clone() },
            documents,
        }
    }
}

#[async_trait]
impl KernelPlugin for TextSearchPlugin {
    fn name(&self) -> &str {
        "TextSearchPlugin"
    }

    fn description(&self) -> &str {
        "Plugin for performing various text search operations"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![
            &self.basic_search as &dyn KernelFunction,
            &self.regex_search as &dyn KernelFunction,
            &self.category_search as &dyn KernelFunction,
            &self.tag_search as &dyn KernelFunction,
            &self.ranked_search as &dyn KernelFunction,
        ]
    }
}

/// Basic text search function
pub struct BasicSearchFunction {
    documents: Vec<TextDocument>,
}

#[async_trait]
impl KernelFunction for BasicSearchFunction {
    fn name(&self) -> &str {
        "basic_search"
    }

    fn description(&self) -> &str {
        "Perform basic text search across document titles and content"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_query = String::new();
        let query = arguments.get("query").unwrap_or(&empty_query);
        let limit = arguments.get("limit")
            .and_then(|s| s.parse::<usize>().ok())
            .unwrap_or(10);

        println!("   🔍 Performing basic search for: '{}'", query);

        let mut results = Vec::new();
        for doc in &self.documents {
            let query_lower = query.to_lowercase();
            if doc.title.to_lowercase().contains(&query_lower) ||
               doc.content.to_lowercase().contains(&query_lower) {
                results.push(json!({
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "word_count": doc.word_count,
                    "snippet": doc.content.chars().take(100).collect::<String>() + "...",
                    "match_type": if doc.title.to_lowercase().contains(&query_lower) { "title" } else { "content" }
                }));
            }
        }

        results.truncate(limit);
        println!("   ✅ Found {} matches", results.len());

        Ok(json!({
            "query": query,
            "total_results": results.len(),
            "results": results,
            "search_type": "basic"
        }).to_string())
    }

    fn get_json_schema(&self) -> serde_json::Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The text to search for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "minimum": 1,
                            "maximum": 100
                        }
                    },
                    "required": ["query"]
                }
            }
        })
    }
}

/// Regex-based search function
pub struct RegexSearchFunction {
    documents: Vec<TextDocument>,
}

#[async_trait]
impl KernelFunction for RegexSearchFunction {
    fn name(&self) -> &str {
        "regex_search"
    }

    fn description(&self) -> &str {
        "Perform pattern-based search using regular expressions"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_pattern = String::new();
        let pattern = arguments.get("pattern").unwrap_or(&empty_pattern);
        let case_sensitive = arguments.get("case_sensitive")
            .map(|s| s.parse::<bool>().unwrap_or(false))
            .unwrap_or(false);

        println!("   🔎 Performing regex search with pattern: '{}'", pattern);

        let regex = if case_sensitive {
            Regex::new(pattern)
        } else {
            Regex::new(&format!("(?i){}", pattern))
        }.map_err(|e| format!("Invalid regex pattern: {}", e))?;

        let mut results = Vec::new();
        for doc in &self.documents {
            let mut matches = Vec::new();
            
            // Search in title
            for mat in regex.find_iter(&doc.title) {
                matches.push(json!({
                    "field": "title",
                    "match": mat.as_str(),
                    "start": mat.start(),
                    "end": mat.end()
                }));
            }
            
            // Search in content
            for mat in regex.find_iter(&doc.content) {
                matches.push(json!({
                    "field": "content", 
                    "match": mat.as_str(),
                    "start": mat.start(),
                    "end": mat.end()
                }));
            }

            if !matches.is_empty() {
                results.push(json!({
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "matches": matches,
                    "match_count": matches.len()
                }));
            }
        }

        println!("   ✅ Found pattern matches in {} documents", results.len());

        Ok(json!({
            "pattern": pattern,
            "case_sensitive": case_sensitive,
            "total_documents_matched": results.len(),
            "results": results,
            "search_type": "regex"
        }).to_string())
    }

    fn get_json_schema(&self) -> serde_json::Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Regular expression pattern to search for"
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Whether the search should be case sensitive",
                            "default": false
                        }
                    },
                    "required": ["pattern"]
                }
            }
        })
    }
}

/// Category-based search function
pub struct CategorySearchFunction {
    documents: Vec<TextDocument>,
}

#[async_trait]
impl KernelFunction for CategorySearchFunction {
    fn name(&self) -> &str {
        "category_search"
    }

    fn description(&self) -> &str {
        "Search documents by category with optional text filtering"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_category = String::new();
        let category = arguments.get("category").unwrap_or(&empty_category);
        let text_filter = arguments.get("text_filter");

        println!("   📂 Searching category: '{}'", category);
        if let Some(filter) = text_filter {
            println!("   🔍 With text filter: '{}'", filter);
        }

        let mut results = Vec::new();
        for doc in &self.documents {
            let category_matches = doc.category.to_lowercase().contains(&category.to_lowercase());
            
            let text_matches = text_filter.map_or(true, |filter| {
                doc.title.to_lowercase().contains(&filter.to_lowercase()) ||
                doc.content.to_lowercase().contains(&filter.to_lowercase())
            });

            if category_matches && text_matches {
                results.push(json!({
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "tags": doc.tags,
                    "word_count": doc.word_count,
                    "created_at": doc.created_at.to_rfc3339(),
                    "snippet": doc.content.chars().take(150).collect::<String>() + "..."
                }));
            }
        }

        println!("   ✅ Found {} documents in category", results.len());

        Ok(json!({
            "category": category,
            "text_filter": text_filter,
            "total_results": results.len(),
            "results": results,
            "search_type": "category"
        }).to_string())
    }

    fn get_json_schema(&self) -> serde_json::Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "Category to search within"
                        },
                        "text_filter": {
                            "type": "string",
                            "description": "Optional text filter to apply within the category"
                        }
                    },
                    "required": ["category"]
                }
            }
        })
    }
}

/// Tag-based search function
pub struct TagSearchFunction {
    documents: Vec<TextDocument>,
}

#[async_trait]
impl KernelFunction for TagSearchFunction {
    fn name(&self) -> &str {
        "tag_search"
    }

    fn description(&self) -> &str {
        "Search documents by tags with support for multiple tag combinations"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_tags = String::new();
        let tags_str = arguments.get("tags").unwrap_or(&empty_tags);
        let match_all = arguments.get("match_all")
            .map(|s| s.parse::<bool>().unwrap_or(false))
            .unwrap_or(false);

        let search_tags: Vec<&str> = tags_str.split(',').map(|s| s.trim()).collect();
        
        println!("   🏷️  Searching for tags: {:?}", search_tags);
        println!("   🔧 Match all tags: {}", match_all);

        let mut results = Vec::new();
        for doc in &self.documents {
            let matching_tags: Vec<&str> = search_tags.iter()
                .filter(|&search_tag| {
                    doc.tags.iter().any(|doc_tag| 
                        doc_tag.to_lowercase().contains(&search_tag.to_lowercase())
                    )
                })
                .copied()
                .collect();

            let matches = if match_all {
                matching_tags.len() == search_tags.len()
            } else {
                !matching_tags.is_empty()
            };

            if matches {
                results.push(json!({
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "all_tags": doc.tags,
                    "matching_tags": matching_tags,
                    "match_ratio": (matching_tags.len() as f64) / (search_tags.len() as f64),
                    "snippet": doc.content.chars().take(120).collect::<String>() + "..."
                }));
            }
        }

        // Sort by match ratio (most relevant first)
        results.sort_by(|a, b| {
            let ratio_a = a["match_ratio"].as_f64().unwrap_or(0.0);
            let ratio_b = b["match_ratio"].as_f64().unwrap_or(0.0);
            ratio_b.partial_cmp(&ratio_a).unwrap_or(std::cmp::Ordering::Equal)
        });

        println!("   ✅ Found {} documents with matching tags", results.len());

        Ok(json!({
            "search_tags": search_tags,
            "match_all": match_all,
            "total_results": results.len(),
            "results": results,
            "search_type": "tag"
        }).to_string())
    }

    fn get_json_schema(&self) -> serde_json::Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tags": {
                            "type": "string",
                            "description": "Comma-separated list of tags to search for"
                        },
                        "match_all": {
                            "type": "boolean",
                            "description": "Whether all tags must match (true) or any tag (false)",
                            "default": false
                        }
                    },
                    "required": ["tags"]
                }
            }
        })
    }
}

/// Ranked search function with relevance scoring
pub struct RankedSearchFunction {
    documents: Vec<TextDocument>,
}

#[async_trait]
impl KernelFunction for RankedSearchFunction {
    fn name(&self) -> &str {
        "ranked_search"
    }

    fn description(&self) -> &str {
        "Perform ranked search with relevance scoring and result ordering"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_query = String::new();
        let query = arguments.get("query").unwrap_or(&empty_query);
        let limit = arguments.get("limit")
            .and_then(|s| s.parse::<usize>().ok())
            .unwrap_or(10);
        let min_score = arguments.get("min_score")
            .and_then(|s| s.parse::<f64>().ok())
            .unwrap_or(0.1);

        println!("   🎯 Performing ranked search for: '{}'", query);
        println!("   📊 Minimum relevance score: {:.2}", min_score);

        let mut scored_results: Vec<(f64, &TextDocument)> = self.documents
            .iter()
            .map(|doc| (doc.relevance_score(query), doc))
            .filter(|(score, _)| *score >= min_score)
            .collect();

        // Sort by relevance score (highest first)
        scored_results.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
        
        // Take only the requested number of results
        scored_results.truncate(limit);

        let results: Vec<serde_json::Value> = scored_results
            .into_iter()
            .enumerate()
            .map(|(rank, (score, doc))| {
                json!({
                    "rank": rank + 1,
                    "id": doc.id,
                    "title": doc.title,
                    "category": doc.category,
                    "tags": doc.tags,
                    "relevance_score": (score * 100.0).round() / 100.0, // Round to 2 decimal places
                    "word_count": doc.word_count,
                    "snippet": doc.content.chars().take(200).collect::<String>() + "...",
                    "created_at": doc.created_at.to_rfc3339()
                })
            })
            .collect();

        println!("   ✅ Ranked {} results by relevance", results.len());

        Ok(json!({
            "query": query,
            "min_score": min_score,
            "total_results": results.len(),
            "results": results,
            "search_type": "ranked",
            "scoring_factors": [
                "Title match (weight: 10x)",
                "Content frequency (weight: 2x)",
                "Tag match (weight: 8x)",
                "Category match (weight: 5x)",
                "Document length normalization"
            ]
        }).to_string())
    }

    fn get_json_schema(&self) -> serde_json::Value {
        json!({
            "type": "function",
            "function": {
                "name": self.name(),
                "description": self.description(),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "minimum": 1,
                            "maximum": 50
                        },
                        "min_score": {
                            "type": "number",
                            "description": "Minimum relevance score threshold",
                            "minimum": 0.0,
                            "maximum": 100.0
                        }
                    },
                    "required": ["query"]
                }
            }
        })
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🔍 Semantic Kernel Rust - Step 01: Basic Text Search");
    println!("===================================================\n");

    // Create kernel with text search plugin
    let text_search_plugin = TextSearchPlugin::new();
    let mut kernel = KernelBuilder::new().build();
    kernel.add_plugin("TextSearchPlugin", Box::new(text_search_plugin));

    // Example 1: Basic text search
    println!("Example 1: Basic Text Search");
    println!("===========================");
    
    basic_text_search(&kernel).await?;

    // Example 2: Pattern-based search with regex
    println!("\nExample 2: Pattern-Based Search (Regex)");
    println!("=====================================");
    
    regex_pattern_search(&kernel).await?;

    // Example 3: Category and tag-based search
    println!("\nExample 3: Category and Tag-Based Search");
    println!("======================================");
    
    category_and_tag_search(&kernel).await?;

    // Example 4: Ranked search with relevance scoring
    println!("\nExample 4: Ranked Search with Relevance Scoring");
    println!("=============================================");
    
    ranked_relevance_search(&kernel).await?;

    println!("\n✅ Text Search examples completed!");

    Ok(())
}

/// Example 1: Basic text search operations
async fn basic_text_search(kernel: &Kernel) -> Result<()> {
    println!("🎯 Performing basic text searches across document collection");
    
    // Get the text search plugin
    if let Some(plugin) = kernel.get_plugin("TextSearchPlugin") {
        let functions = plugin.functions();
        
        // Find the basic search function
        for function in &functions {
            if function.name() == "basic_search" {
                // Search for programming-related content
                let mut args = HashMap::new();
                args.insert("query".to_string(), "programming".to_string());
                args.insert("limit".to_string(), "3".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Search error: {}", e))?;
                println!("📋 Programming search results:\n{}\n", result);
                
                // Search for machine learning content
                args.clear();
                args.insert("query".to_string(), "machine learning".to_string());
                args.insert("limit".to_string(), "2".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Search error: {}", e))?;
                println!("📋 Machine Learning search results:\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 2: Pattern-based search using regular expressions
async fn regex_pattern_search(kernel: &Kernel) -> Result<()> {
    println!("🎯 Using regex patterns to find specific text patterns");
    
    if let Some(plugin) = kernel.get_plugin("TextSearchPlugin") {
        let functions = plugin.functions();
        
        for function in &functions {
            if function.name() == "regex_search" {
                // Search for programming languages (case-insensitive)
                let mut args = HashMap::new();
                args.insert("pattern".to_string(), r"\b(rust|python|javascript|java)\b".to_string());
                args.insert("case_sensitive".to_string(), "false".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Regex search error: {}", e))?;
                println!("📋 Programming language pattern matches:\n{}\n", result);
                
                // Search for version numbers or technical terms
                args.clear();
                args.insert("pattern".to_string(), r"\b[A-Z][a-z]+[A-Z][a-z]+".to_string()); // CamelCase terms
                args.insert("case_sensitive".to_string(), "true".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Regex search error: {}", e))?;
                println!("📋 CamelCase term matches:\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 3: Category and tag-based search
async fn category_and_tag_search(kernel: &Kernel) -> Result<()> {
    println!("🎯 Searching by categories and tags for targeted results");
    
    if let Some(plugin) = kernel.get_plugin("TextSearchPlugin") {
        let functions = plugin.functions();
        
        // Category search
        for function in &functions {
            if function.name() == "category_search" {
                let mut args = HashMap::new();
                args.insert("category".to_string(), "Programming".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Category search error: {}", e))?;
                println!("📂 Programming category results:\n{}\n", result);
                
                // Category search with text filter
                args.insert("text_filter".to_string(), "safety".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Category search error: {}", e))?;
                println!("📂 Programming + safety filter results:\n{}\n", result);
                
                break;
            }
        }
        
        // Tag search
        for function in &functions {
            if function.name() == "tag_search" {
                let mut args = HashMap::new();
                args.insert("tags".to_string(), "python,ml".to_string());
                args.insert("match_all".to_string(), "false".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Tag search error: {}", e))?;
                println!("🏷️  Tag search (any match) results:\n{}\n", result);
                
                // Search requiring all tags
                args.insert("tags".to_string(), "cloud,aws".to_string());
                args.insert("match_all".to_string(), "true".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Tag search error: {}", e))?;
                println!("🏷️  Tag search (all must match) results:\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 4: Ranked search with relevance scoring
async fn ranked_relevance_search(kernel: &Kernel) -> Result<()> {
    println!("🎯 Performing relevance-ranked search with scoring");
    
    if let Some(plugin) = kernel.get_plugin("TextSearchPlugin") {
        let functions = plugin.functions();
        
        for function in &functions {
            if function.name() == "ranked_search" {
                // High-relevance search
                let mut args = HashMap::new();
                args.insert("query".to_string(), "database".to_string());
                args.insert("limit".to_string(), "5".to_string());
                args.insert("min_score".to_string(), "1.0".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Ranked search error: {}", e))?;
                println!("🎯 High-relevance database search:\n{}\n", result);
                
                // Broader search with lower threshold
                args.insert("query".to_string(), "development".to_string());
                args.insert("limit".to_string(), "4".to_string());
                args.insert("min_score".to_string(), "0.5".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Ranked search error: {}", e))?;
                println!("🎯 Broader development search:\n{}\n", result);
                
                // Multi-word query
                args.insert("query".to_string(), "machine learning python".to_string());
                args.insert("limit".to_string(), "3".to_string());
                args.insert("min_score".to_string(), "2.0".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Ranked search error: {}", e))?;
                println!("🎯 Multi-word relevance search:\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}