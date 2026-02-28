//! Step 02: Text Analysis with NLP Patterns
//! 
//! This example demonstrates natural language processing and text analysis capabilities.
//! It showcases:
//! - Sentiment analysis and classification
//! - Text summarization with different strategies
//! - Keyword extraction and entity recognition
//! - Language detection and text statistics
//! - Readability analysis and text quality metrics
//! - Content classification and topic modeling

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use semantic_kernel::kernel::{KernelPlugin, KernelFunction};
use semantic_kernel::async_trait;
use std::collections::HashMap;
use serde_json::json;
use regex::Regex;

/// Text analysis document with rich metadata
#[derive(Debug, Clone)]
pub struct AnalysisDocument {
    pub id: String,
    pub title: String,
    pub content: String,
    pub author: Option<String>,
    pub language: String,
    pub word_count: usize,
    pub sentence_count: usize,
    pub paragraph_count: usize,
    pub created_at: chrono::DateTime<chrono::Utc>,
}

impl AnalysisDocument {
    pub fn new(id: String, title: String, content: String, author: Option<String>) -> Self {
        let word_count = content.split_whitespace().count();
        let sentence_count = content.split(&['.', '!', '?']).filter(|s| !s.trim().is_empty()).count();
        let paragraph_count = content.split("\n\n").filter(|s| !s.trim().is_empty()).count().max(1);
        
        Self {
            id,
            title,
            content,
            author,
            language: "en".to_string(), // Default to English for demo
            word_count,
            sentence_count,
            paragraph_count,
            created_at: chrono::Utc::now(),
        }
    }

    /// Calculate average words per sentence
    pub fn avg_words_per_sentence(&self) -> f64 {
        if self.sentence_count > 0 {
            self.word_count as f64 / self.sentence_count as f64
        } else {
            0.0
        }
    }

    /// Calculate readability score (simplified Flesch formula)
    pub fn readability_score(&self) -> f64 {
        let avg_sentence_length = self.avg_words_per_sentence();
        let avg_syllables_per_word = 1.5; // Simplified estimate
        
        // Flesch Reading Ease Score
        206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    }

    /// Classify readability level
    pub fn readability_level(&self) -> &'static str {
        let score = self.readability_score();
        match score {
            s if s >= 90.0 => "Very Easy",
            s if s >= 80.0 => "Easy", 
            s if s >= 70.0 => "Fairly Easy",
            s if s >= 60.0 => "Standard",
            s if s >= 50.0 => "Fairly Difficult",
            s if s >= 30.0 => "Difficult",
            _ => "Very Difficult"
        }
    }
}

/// Text analysis plugin providing NLP capabilities
pub struct TextAnalysisPlugin {
    documents: Vec<AnalysisDocument>,
    sentiment_analyzer: SentimentAnalyzer,
    summarizer: TextSummarizer,
    keyword_extractor: KeywordExtractor,
    classifier: ContentClassifier,
    statistics_analyzer: TextStatistics,
}

impl TextAnalysisPlugin {
    pub fn new() -> Self {
        // Create sample documents for analysis
        let documents = vec![
            AnalysisDocument::new(
                "review1".to_string(),
                "Product Review - Excellent Quality".to_string(),
                "I absolutely love this product! The quality is outstanding and it exceeded all my expectations. The customer service was fantastic, and delivery was prompt. I would definitely recommend this to anyone looking for a reliable solution. Five stars!".to_string(),
                Some("Customer A".to_string())
            ),
            AnalysisDocument::new(
                "review2".to_string(),
                "Disappointing Experience".to_string(),
                "Unfortunately, this product did not meet my expectations. The build quality feels cheap and the functionality is limited. I experienced several issues during setup and the support team was not helpful. I would not purchase this again.".to_string(),
                Some("Customer B".to_string())
            ),
            AnalysisDocument::new(
                "article1".to_string(),
                "The Future of Artificial Intelligence".to_string(),
                "Artificial Intelligence is rapidly transforming industries across the globe. Machine learning algorithms are becoming more sophisticated, enabling automation of complex tasks. Natural language processing has advanced significantly, allowing computers to understand and generate human-like text. Computer vision systems can now identify objects with remarkable accuracy. The integration of AI into daily life continues to accelerate, bringing both opportunities and challenges for society.".to_string(),
                Some("Tech Writer".to_string())
            ),
            AnalysisDocument::new(
                "story1".to_string(),
                "A Short Adventure".to_string(),
                "The old lighthouse stood majestically on the cliff, its beacon cutting through the foggy night. Sarah approached cautiously, her flashlight casting eerie shadows on the weathered stones. Inside, she discovered an ancient journal filled with mysterious entries about ships that had vanished decades ago. As thunder rolled overhead, she realized she wasn't alone in the lighthouse.".to_string(),
                Some("Story Author".to_string())
            ),
            AnalysisDocument::new(
                "academic1".to_string(),
                "Climate Change Impact Analysis".to_string(),
                "This comprehensive study examines the multifaceted impacts of climate change on global ecosystems. The research methodology employed longitudinal data analysis spanning three decades. Results indicate significant correlations between temperature variations and biodiversity indices. Statistical analysis reveals concerning trends in species migration patterns. The implications for conservation strategies are substantial and warrant immediate attention from policymakers.".to_string(),
                Some("Dr. Researcher".to_string())
            ),
        ];
        
        Self {
            sentiment_analyzer: SentimentAnalyzer::new(),
            summarizer: TextSummarizer::new(),
            keyword_extractor: KeywordExtractor::new(),
            classifier: ContentClassifier::new(),
            statistics_analyzer: TextStatistics::new(),
            documents,
        }
    }
}

#[async_trait]
impl KernelPlugin for TextAnalysisPlugin {
    fn name(&self) -> &str {
        "TextAnalysisPlugin"
    }

    fn description(&self) -> &str {
        "Plugin for performing advanced text analysis and NLP operations"
    }

    fn functions(&self) -> Vec<&dyn KernelFunction> {
        vec![
            &self.sentiment_analyzer as &dyn KernelFunction,
            &self.summarizer as &dyn KernelFunction,
            &self.keyword_extractor as &dyn KernelFunction,
            &self.classifier as &dyn KernelFunction,
            &self.statistics_analyzer as &dyn KernelFunction,
        ]
    }
}

/// Sentiment analysis function
pub struct SentimentAnalyzer {
    positive_words: Vec<&'static str>,
    negative_words: Vec<&'static str>,
}

impl SentimentAnalyzer {
    pub fn new() -> Self {
        Self {
            positive_words: vec![
                "excellent", "outstanding", "fantastic", "love", "great", "amazing", "wonderful",
                "perfect", "brilliant", "impressive", "superb", "marvelous", "delighted", "satisfied",
                "recommend", "pleased", "happy", "good", "best", "incredible", "awesome"
            ],
            negative_words: vec![
                "disappointing", "terrible", "awful", "horrible", "bad", "worst", "hate", "poor",
                "cheap", "limited", "issues", "problems", "failed", "broken", "difficult", "slow",
                "expensive", "complicated", "frustrated", "annoying", "useless"
            ],
        }
    }

    fn analyze_sentiment(&self, text: &str) -> (f64, String, HashMap<String, i32>) {
        let text_lower = text.to_lowercase();
        let words: Vec<&str> = text_lower.split_whitespace().collect();
        
        let mut positive_count = 0;
        let mut negative_count = 0;
        let mut word_matches = HashMap::new();
        
        for word in &words {
            if self.positive_words.contains(word) {
                positive_count += 1;
                *word_matches.entry(format!("positive:{}", word)).or_insert(0) += 1;
            }
            if self.negative_words.contains(word) {
                negative_count += 1;
                *word_matches.entry(format!("negative:{}", word)).or_insert(0) += 1;
            }
        }
        
        let total_sentiment_words = positive_count + negative_count;
        let sentiment_score = if total_sentiment_words > 0 {
            (positive_count as f64 - negative_count as f64) / total_sentiment_words as f64
        } else {
            0.0
        };
        
        let sentiment_label = match sentiment_score {
            s if s > 0.3 => "Positive",
            s if s < -0.3 => "Negative", 
            _ => "Neutral"
        };
        
        (sentiment_score, sentiment_label.to_string(), word_matches)
    }
}

#[async_trait]
impl KernelFunction for SentimentAnalyzer {
    fn name(&self) -> &str {
        "analyze_sentiment"
    }

    fn description(&self) -> &str {
        "Analyze the sentiment of text content (positive, negative, neutral)"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_text = String::new();
        let text = arguments.get("text").unwrap_or(&empty_text);
        let include_details = arguments.get("include_details")
            .map(|s| s.parse::<bool>().unwrap_or(false))
            .unwrap_or(false);

        println!("   😊 Analyzing sentiment for {} characters of text", text.len()); 
        
        let (score, label, word_matches) = self.analyze_sentiment(text);
        
        println!("   📊 Sentiment: {} (score: {:.2})", label, score);
        
        let mut result = json!({
            "sentiment_score": (score * 100.0).round() / 100.0,
            "sentiment_label": label,
            "text_length": text.len(),
            "analysis_type": "sentiment"
        });
        
        if include_details {
            result["word_matches"] = json!(word_matches);
            result["total_sentiment_words"] = json!(word_matches.len());
        }
        
        Ok(result.to_string())
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
                        "text": {
                            "type": "string",
                            "description": "The text to analyze for sentiment"
                        },
                        "include_details": {
                            "type": "boolean",
                            "description": "Whether to include detailed word matches",
                            "default": false
                        }
                    },
                    "required": ["text"]
                }
            }
        })
    }
}

/// Text summarization function
pub struct TextSummarizer;

impl TextSummarizer {
    pub fn new() -> Self {
        Self
    }

    fn extractive_summarization(&self, text: &str, max_sentences: usize) -> Vec<String> {
        let sentences: Vec<&str> = text.split(&['.', '!', '?']).collect();
        let cleaned_sentences: Vec<String> = sentences.iter()
            .map(|s| s.trim().to_string())
            .filter(|s| !s.is_empty() && s.len() > 10)
            .collect();
        
        // Simple scoring based on sentence length and position
        let mut scored_sentences: Vec<(usize, String, f64)> = cleaned_sentences.iter()
            .enumerate()
            .map(|(i, s)| {
                let word_count = s.split_whitespace().count();
                let position_score = if i == 0 { 1.5 } else { 1.0 }; // First sentence bonus
                let length_score = (word_count as f64).min(20.0) / 20.0; // Prefer moderate length
                (i, s.clone(), position_score * length_score)
            })
            .collect();
        
        // Sort by score and take top sentences
        scored_sentences.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap_or(std::cmp::Ordering::Equal));
        scored_sentences.truncate(max_sentences);
        
        // Sort by original order
        scored_sentences.sort_by_key(|x| x.0);
        scored_sentences.into_iter().map(|(_, sentence, _)| sentence).collect()
    }
}

#[async_trait]
impl KernelFunction for TextSummarizer {
    fn name(&self) -> &str {
        "summarize_text"
    }

    fn description(&self) -> &str {
        "Generate extractive summaries of text content"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_text = String::new();
        let text = arguments.get("text").unwrap_or(&empty_text);
        let max_sentences = arguments.get("max_sentences")
            .and_then(|s| s.parse::<usize>().ok())
            .unwrap_or(3);

        println!("   📝 Summarizing text to {} sentences", max_sentences);
        
        let summary_sentences = self.extractive_summarization(text, max_sentences);
        let summary = summary_sentences.join(". ") + ".";
        
        let original_word_count = text.split_whitespace().count();
        let summary_word_count = summary.split_whitespace().count();
        let compression_ratio = if original_word_count > 0 {
            (summary_word_count as f64 / original_word_count as f64 * 100.0).round()
        } else {
            0.0
        };
        
        println!("   ✅ Generated summary with {:.0}% compression", compression_ratio);
        
        Ok(json!({
            "summary": summary,
            "original_word_count": original_word_count,
            "summary_word_count": summary_word_count,
            "compression_ratio": compression_ratio,
            "sentences_extracted": summary_sentences.len(),
            "analysis_type": "summarization"
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
                        "text": {
                            "type": "string",
                            "description": "The text to summarize"
                        },
                        "max_sentences": {
                            "type": "integer",
                            "description": "Maximum number of sentences in summary",
                            "minimum": 1,
                            "maximum": 10
                        }
                    },
                    "required": ["text"]
                }
            }
        })
    }
}

/// Keyword extraction function
pub struct KeywordExtractor;

impl KeywordExtractor {
    pub fn new() -> Self {
        Self
    }

    fn extract_keywords(&self, text: &str, limit: usize) -> Vec<(String, i32)> {
        let stop_words = vec![
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "must", "can", "this",
            "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "my", "your",
            "his", "her", "its", "our", "their", "me", "him", "her", "us", "them", "not", "no"
        ];
        
        let text_lower = text.to_lowercase();
        let re = Regex::new(r"[^\w\s]").unwrap();
        let cleaned_text = re.replace_all(&text_lower, "");
        
        let words: Vec<&str> = cleaned_text.split_whitespace().collect();
        let mut word_freq = HashMap::new();
        
        for word in words {
            if word.len() > 2 && !stop_words.contains(&word) {
                *word_freq.entry(word.to_string()).or_insert(0) += 1;
            }
        }
        
        let mut keywords: Vec<(String, i32)> = word_freq.into_iter().collect();
        keywords.sort_by(|a, b| b.1.cmp(&a.1));
        keywords.truncate(limit);
        
        keywords
    }
}

#[async_trait]
impl KernelFunction for KeywordExtractor {
    fn name(&self) -> &str {
        "extract_keywords"
    }

    fn description(&self) -> &str {
        "Extract important keywords and phrases from text"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_text = String::new();
        let text = arguments.get("text").unwrap_or(&empty_text);
        let limit = arguments.get("limit")
            .and_then(|s| s.parse::<usize>().ok())
            .unwrap_or(10);

        println!("   🔑 Extracting top {} keywords", limit);
        
        let keywords = self.extract_keywords(text, limit);
        
        println!("   ✅ Found {} unique keywords", keywords.len());
        
        Ok(json!({
            "keywords": keywords.iter().map(|(word, freq)| json!({
                "word": word,
                "frequency": freq,
                "relevance_score": (*freq as f64) / text.split_whitespace().count() as f64 * 100.0
            })).collect::<Vec<_>>(),
            "total_keywords": keywords.len(),
            "text_length": text.len(),
            "analysis_type": "keyword_extraction"
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
                        "text": {
                            "type": "string",
                            "description": "The text to extract keywords from"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of keywords to extract",
                            "minimum": 1,
                            "maximum": 50
                        }
                    },
                    "required": ["text"]
                }
            }
        })
    }
}

/// Content classification function
pub struct ContentClassifier;

impl ContentClassifier {
    pub fn new() -> Self {
        Self
    }

    fn classify_content(&self, text: &str, title: Option<&str>) -> (String, f64, HashMap<String, f64>) {
        let text_lower = text.to_lowercase();
        let title_lower = title.map(|t| t.to_lowercase()).unwrap_or_default();
        
        let mut category_scores = HashMap::new();
        
        // Technical/Academic patterns
        let technical_indicators = vec![
            "algorithm", "system", "method", "analysis", "research", "study", "data", "model",
            "framework", "implementation", "evaluation", "results", "conclusion", "abstract",
            "methodology", "statistical", "correlation", "hypothesis", "experiment"
        ];
        
        // Review/Opinion patterns
        let review_indicators = vec![
            "recommend", "experience", "quality", "service", "product", "customer", "purchase",
            "delivery", "rating", "review", "opinion", "satisfied", "disappointed", "excellent",
            "terrible", "stars", "would", "should", "definitely"
        ];
        
        // Narrative/Creative patterns
        let narrative_indicators = vec![
            "story", "character", "scene", "chapter", "plot", "adventure", "mysterious", "ancient",
            "suddenly", "whispered", "shadow", "journey", "discovered", "realized", "appeared",
            "walked", "looked", "felt", "heard", "saw"
        ];
        
        // News/Information patterns
        let news_indicators = vec![
            "according", "report", "announced", "officials", "government", "policy", "economic",
            "market", "industry", "company", "global", "international", "development", "impact",
            "future", "trend", "growth", "change"
        ];
        
        let all_text = format!("{} {}", title_lower, text_lower);
        
        // Score each category
        category_scores.insert("Technical/Academic".to_string(), 
            self.calculate_category_score(&all_text, &technical_indicators));
        category_scores.insert("Review/Opinion".to_string(), 
            self.calculate_category_score(&all_text, &review_indicators));
        category_scores.insert("Narrative/Creative".to_string(), 
            self.calculate_category_score(&all_text, &narrative_indicators));
        category_scores.insert("News/Information".to_string(), 
            self.calculate_category_score(&all_text, &news_indicators));
        
        // Find best match
        let best_category = category_scores.iter()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap_or(std::cmp::Ordering::Equal))
            .map(|(category, score)| (category.clone(), *score))
            .unwrap_or(("Unknown".to_string(), 0.0));
        
        (best_category.0, best_category.1, category_scores)
    }
    
    fn calculate_category_score(&self, text: &str, indicators: &[&str]) -> f64 {
        let words: Vec<&str> = text.split_whitespace().collect();
        let total_words = words.len() as f64;
        
        if total_words == 0.0 {
            return 0.0;
        }
        
        let matches = indicators.iter()
            .map(|&indicator| text.matches(indicator).count())
            .sum::<usize>() as f64;
        
        (matches / total_words) * 100.0
    }
}

#[async_trait]
impl KernelFunction for ContentClassifier {
    fn name(&self) -> &str {
        "classify_content"
    }

    fn description(&self) -> &str {
        "Classify text content into categories (Technical, Review, Narrative, News)"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_text = String::new();
        let text = arguments.get("text").unwrap_or(&empty_text);
        let title = arguments.get("title");

        println!("   🏷️  Classifying content type");
        
        let (category, confidence, all_scores) = self.classify_content(text, title.map(|s| s.as_str()));
        
        println!("   📊 Classification: {} ({:.1}% confidence)", category, confidence);
        
        Ok(json!({
            "predicted_category": category,
            "confidence_score": (confidence * 10.0).round() / 10.0,
            "all_category_scores": all_scores,
            "text_length": text.len(),
            "analysis_type": "content_classification"
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
                        "text": {
                            "type": "string",
                            "description": "The text content to classify"
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title to aid classification"
                        }
                    },
                    "required": ["text"]
                }
            }
        })
    }
}

/// Text statistics analysis function
pub struct TextStatistics;

impl TextStatistics {
    pub fn new() -> Self {
        Self
    }

    fn analyze_statistics(&self, text: &str, title: Option<&str>) -> serde_json::Value {
        let char_count = text.len();
        let word_count = text.split_whitespace().count();
        let sentence_count = text.split(&['.', '!', '?']).filter(|s| !s.trim().is_empty()).count();
        let paragraph_count = text.split("\n\n").filter(|s| !s.trim().is_empty()).count().max(1);
        
        let avg_word_length = if word_count > 0 {
            text.split_whitespace().map(|w| w.len()).sum::<usize>() as f64 / word_count as f64
        } else {
            0.0
        };
        
        let avg_sentence_length = if sentence_count > 0 {
            word_count as f64 / sentence_count as f64
        } else {
            0.0
        };
        
        // Simple readability score (Flesch approximation)
        let readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * 1.5);
        let readability_level = match readability_score {
            s if s >= 90.0 => "Very Easy",
            s if s >= 80.0 => "Easy",
            s if s >= 70.0 => "Fairly Easy", 
            s if s >= 60.0 => "Standard",
            s if s >= 50.0 => "Fairly Difficult",
            s if s >= 30.0 => "Difficult",
            _ => "Very Difficult"
        };
        
        json!({
            "basic_stats": {
                "character_count": char_count,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count
            },
            "averages": {
                "avg_word_length": (avg_word_length * 10.0).round() / 10.0,
                "avg_sentence_length": (avg_sentence_length * 10.0).round() / 10.0,
                "avg_words_per_paragraph": if paragraph_count > 0 { 
                    (word_count as f64 / paragraph_count as f64 * 10.0).round() / 10.0 
                } else { 
                    0.0 
                }
            },
            "readability": {
                "flesch_score": (readability_score * 10.0).round() / 10.0,
                "reading_level": readability_level,
                "estimated_reading_time_minutes": ((word_count as f64 / 200.0) * 10.0).round() / 10.0
            },
            "has_title": title.is_some(),
            "title_length": title.map(|t| t.len()).unwrap_or(0)
        })
    }
}

#[async_trait]
impl KernelFunction for TextStatistics {
    fn name(&self) -> &str {
        "analyze_statistics"
    }

    fn description(&self) -> &str {
        "Analyze text statistics including readability, word counts, and structure"
    }

    async fn invoke(&self, _kernel: &Kernel, arguments: &HashMap<String, String>) -> semantic_kernel::Result<String> {
        let empty_text = String::new();
        let text = arguments.get("text").unwrap_or(&empty_text);
        let title = arguments.get("title");

        println!("   📊 Analyzing text statistics");
        
        let statistics = self.analyze_statistics(text, title.map(|s| s.as_str()));
        
        let word_count = statistics["basic_stats"]["word_count"].as_u64().unwrap_or(0);
        let reading_level = statistics["readability"]["reading_level"].as_str().unwrap_or("Unknown");
        
        println!("   ✅ Analyzed {} words - Reading level: {}", word_count, reading_level);
        
        let mut result = statistics;
        result["analysis_type"] = json!("text_statistics");
        
        Ok(result.to_string())
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
                        "text": {
                            "type": "string",
                            "description": "The text to analyze"
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title for additional context"
                        }
                    },
                    "required": ["text"]
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

    println!("📊 Semantic Kernel Rust - Step 02: Text Analysis with NLP");
    println!("========================================================\n");

    // Create kernel with text analysis plugin
    let text_analysis_plugin = TextAnalysisPlugin::new();
    let mut kernel = KernelBuilder::new().build();
    kernel.add_plugin("TextAnalysisPlugin", Box::new(text_analysis_plugin));

    // Example 1: Sentiment analysis
    println!("Example 1: Sentiment Analysis");
    println!("=============================");
    
    sentiment_analysis_examples(&kernel).await?;

    // Example 2: Text summarization
    println!("\nExample 2: Text Summarization");
    println!("============================");
    
    text_summarization_examples(&kernel).await?;

    // Example 3: Keyword extraction
    println!("\nExample 3: Keyword Extraction");
    println!("============================");
    
    keyword_extraction_examples(&kernel).await?;

    // Example 4: Content classification
    println!("\nExample 4: Content Classification");
    println!("================================");
    
    content_classification_examples(&kernel).await?;

    // Example 5: Text statistics and readability
    println!("\nExample 5: Text Statistics and Readability");
    println!("=========================================");
    
    text_statistics_examples(&kernel).await?;

    println!("\n✅ Text Analysis examples completed!");

    Ok(())
}

/// Example 1: Sentiment analysis of different text types
async fn sentiment_analysis_examples(kernel: &Kernel) -> Result<()> {
    println!("🎯 Analyzing sentiment across different text types");
    
    if let Some(plugin) = kernel.get_plugin("TextAnalysisPlugin") {
        let functions = plugin.functions();
        
        for function in &functions {
            if function.name() == "analyze_sentiment" {
                // Positive review
                let mut args = HashMap::new();
                args.insert("text".to_string(), "I absolutely love this product! The quality is outstanding and it exceeded all my expectations. The customer service was fantastic!".to_string());
                args.insert("include_details".to_string(), "true".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Sentiment analysis error: {}", e))?;
                println!("📈 Positive review analysis:\n{}\n", result);
                
                // Negative review
                args.clear();
                args.insert("text".to_string(), "Unfortunately, this product did not meet my expectations. The build quality feels cheap and the functionality is limited. Very disappointed.".to_string());
                args.insert("include_details".to_string(), "false".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Sentiment analysis error: {}", e))?;
                println!("📉 Negative review analysis:\n{}\n", result);
                
                // Neutral technical text
                args.clear();
                args.insert("text".to_string(), "This system implements a machine learning algorithm for data processing. The methodology involves statistical analysis of patterns.".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Sentiment analysis error: {}", e))?;
                println!("⚖️  Neutral technical text analysis:\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 2: Text summarization with different lengths
async fn text_summarization_examples(kernel: &Kernel) -> Result<()> {
    println!("🎯 Demonstrating text summarization capabilities");
    
    if let Some(plugin) = kernel.get_plugin("TextAnalysisPlugin") {
        let functions = plugin.functions();
        
        for function in &functions {
            if function.name() == "summarize_text" {
                let long_text = "Artificial Intelligence is rapidly transforming industries across the globe. Machine learning algorithms are becoming more sophisticated, enabling automation of complex tasks. Natural language processing has advanced significantly, allowing computers to understand and generate human-like text. Computer vision systems can now identify objects with remarkable accuracy. The integration of AI into daily life continues to accelerate, bringing both opportunities and challenges for society. Companies are investing heavily in AI research and development. Educational institutions are adapting their curricula to include AI and machine learning courses. Governments are developing policies to regulate AI development and deployment.";
                
                // Short summary
                let mut args = HashMap::new();
                args.insert("text".to_string(), long_text.to_string());
                args.insert("max_sentences".to_string(), "2".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Summarization error: {}", e))?;
                println!("📄 Short summary (2 sentences):\n{}\n", result);
                
                // Medium summary
                args.insert("max_sentences".to_string(), "4".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Summarization error: {}", e))?;
                println!("📄 Medium summary (4 sentences):\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 3: Keyword extraction from different content types
async fn keyword_extraction_examples(kernel: &Kernel) -> Result<()> {
    println!("🎯 Extracting keywords from various content types");
    
    if let Some(plugin) = kernel.get_plugin("TextAnalysisPlugin") {
        let functions = plugin.functions();
        
        for function in &functions {
            if function.name() == "extract_keywords" {
                // Technical content
                let mut args = HashMap::new();
                args.insert("text".to_string(), "Machine learning algorithms process large datasets to identify patterns and make predictions. Deep learning neural networks can recognize complex features in images and text. Natural language processing enables computers to understand human language.".to_string());
                args.insert("limit".to_string(), "8".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Keyword extraction error: {}", e))?;
                println!("🔬 Technical content keywords:\n{}\n", result);
                
                // Creative content
                args.clear();
                args.insert("text".to_string(), "The old lighthouse stood majestically on the cliff, its beacon cutting through the foggy night. Sarah approached cautiously, her flashlight casting eerie shadows on the weathered stones. Inside, she discovered an ancient journal filled with mysterious entries.".to_string());
                args.insert("limit".to_string(), "6".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Keyword extraction error: {}", e))?;
                println!("📚 Creative content keywords:\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 4: Content classification
async fn content_classification_examples(kernel: &Kernel) -> Result<()> {
    println!("🎯 Classifying different types of content");
    
    if let Some(plugin) = kernel.get_plugin("TextAnalysisPlugin") {
        let functions = plugin.functions();
        
        for function in &functions {
            if function.name() == "classify_content" {
                let test_cases = vec![
                    ("Academic Research", "This comprehensive study examines the multifaceted impacts of climate change on global ecosystems. The research methodology employed longitudinal data analysis spanning three decades."),
                    ("Product Review", "I absolutely love this product! The quality is outstanding and it exceeded all my expectations. The customer service was fantastic, and delivery was prompt."),
                    ("Creative Story", "The old lighthouse stood majestically on the cliff, its beacon cutting through the foggy night. Sarah approached cautiously, her flashlight casting eerie shadows."),
                    ("News Article", "According to recent reports, the technology industry is experiencing significant growth. Companies are announcing major investments in artificial intelligence development.")
                ];
                
                for (title, content) in test_cases {
                    let mut args = HashMap::new();
                    args.insert("text".to_string(), content.to_string());
                    args.insert("title".to_string(), title.to_string());
                    
                    let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Classification error: {}", e))?;
                    println!("📋 Classifying '{}': \n{}\n", title, result);
                }
                
                break;
            }
        }
    }
    
    Ok(())
}

/// Example 5: Text statistics and readability analysis
async fn text_statistics_examples(kernel: &Kernel) -> Result<()> {
    println!("🎯 Analyzing text statistics and readability metrics");
    
    if let Some(plugin) = kernel.get_plugin("TextAnalysisPlugin") {
        let functions = plugin.functions();
        
        for function in &functions {
            if function.name() == "analyze_statistics" {
                // Simple text
                let mut args = HashMap::new();
                args.insert("text".to_string(), "This is a simple sentence. It is easy to read. The words are short.".to_string());
                args.insert("title".to_string(), "Simple Text Example".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Statistics analysis error: {}", e))?;
                println!("📊 Simple text statistics:\n{}\n", result);
                
                // Complex academic text
                args.clear();
                args.insert("text".to_string(), "The multidisciplinary investigation encompasses comprehensive methodological approaches to quantitative analysis. Statistical correlations demonstrate significant relationships between environmental variables and biodiversity indices. The implications of these findings necessitate immediate policy interventions.".to_string());
                args.insert("title".to_string(), "Academic Research Paper".to_string());
                
                let result = function.invoke(kernel, &args).await.map_err(|e| anyhow::anyhow!("Statistics analysis error: {}", e))?;
                println!("📊 Complex academic text statistics:\n{}\n", result);
                
                break;
            }
        }
    }
    
    Ok(())
}