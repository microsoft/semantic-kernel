//! Step 01: Sequential Planner Example
//! 
//! This example demonstrates sequential planning concepts by creating and executing
//! step-by-step plans to achieve complex goals. It showcases:
//! - Manual plan creation and step sequencing
//! - Context passing between sequential steps
//! - Dynamic plan execution with intermediate results
//! - Goal-oriented task orchestration
//! - Multi-step reasoning patterns

use anyhow::Result;
// Core planning concepts demonstration
use std::collections::HashMap;

/// A simple calculator that can perform basic math operations
pub struct Calculator {
    memory: f64,
}

impl Calculator {
    pub fn new() -> Self {
        Self { memory: 0.0 }
    }
    
    pub fn add(&mut self, a: f64, b: f64) -> f64 {
        let result = a + b;
        self.memory = result;
        println!("   ➕ Adding {} + {} = {}", a, b, result);
        result
    }
    
    pub fn multiply(&mut self, a: f64, b: f64) -> f64 {
        let result = a * b;
        self.memory = result;
        println!("   ✖️  Multiplying {} × {} = {}", a, b, result);
        result
    }
    
    pub fn format_currency(&self, amount: f64) -> String {
        let formatted = format!("${:.2}", amount);
        println!("   💰 Formatting {} as currency: {}", amount, formatted);
        formatted
    }
    
    pub fn compound_interest(&mut self, principal: f64, rate: f64, time: f64) -> f64 {
        // A = P(1 + r)^t
        let result = principal * (1.0 + rate).powf(time);
        self.memory = result;
        println!("   📈 Compound interest: ${:.2} at {:.1}% for {} years = ${:.2}", 
                 principal, rate * 100.0, time, result);
        result
    }
    
    pub fn get_memory(&self) -> f64 {
        self.memory
    }
}

/// Represents a computational step in our plan
#[derive(Debug, Clone)]
pub struct ComputationStep {
    pub name: String,
    pub description: String,
    pub operation: String,
    pub parameters: HashMap<String, f64>,
}

impl ComputationStep {
    pub fn new(name: impl Into<String>, description: impl Into<String>, operation: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            operation: operation.into(),
            parameters: HashMap::new(),
        }
    }
    
    pub fn with_parameter(mut self, key: impl Into<String>, value: f64) -> Self {
        self.parameters.insert(key.into(), value);
        self
    }
    
    pub async fn execute(&self, calculator: &mut Calculator) -> Result<f64> {
        match self.operation.as_str() {
            "add" => {
                let a = self.parameters.get("a").copied().unwrap_or(0.0);
                let b = self.parameters.get("b").copied().unwrap_or(0.0);
                Ok(calculator.add(a, b))
            }
            "multiply" => {
                let a = self.parameters.get("a").copied().unwrap_or(0.0);
                let b = self.parameters.get("b").copied().unwrap_or(0.0);
                Ok(calculator.multiply(a, b))
            }
            "compound_interest" => {
                let principal = self.parameters.get("principal").copied().unwrap_or(0.0);
                let rate = self.parameters.get("rate").copied().unwrap_or(0.0);
                let time = self.parameters.get("time").copied().unwrap_or(0.0);
                Ok(calculator.compound_interest(principal, rate, time))
            }
            _ => Err(anyhow::anyhow!("Unknown operation: {}", self.operation))
        }
    }
}

/// A sequential plan that executes computation steps in order
pub struct SequentialComputationPlan {
    pub name: String,
    pub description: String,
    pub steps: Vec<ComputationStep>,
}

impl SequentialComputationPlan {
    pub fn new(name: impl Into<String>, description: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            description: description.into(),
            steps: Vec::new(),
        }
    }
    
    pub fn add_step(mut self, step: ComputationStep) -> Self {
        self.steps.push(step);
        self
    }
    
    pub async fn execute(&self, calculator: &mut Calculator) -> Result<f64> {
        println!("🚀 Executing plan: {}", self.name);
        println!("📋 Description: {}", self.description);
        println!("📊 Steps: {}", self.steps.len());
        
        let mut last_result = 0.0;
        
        for (i, step) in self.steps.iter().enumerate() {
            println!("\n--- Step {} ---", i + 1);
            println!("🔧 {}: {}", step.name, step.description);
            
            last_result = step.execute(calculator).await?;
            
            println!("✅ Step {} completed with result: {}", i + 1, last_result);
        }
        
        Ok(last_result)
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🧠 Semantic Kernel Rust - Step 01: Sequential Planner");
    println!("=====================================================\n");

    // Example 1: Simple mathematical sequence
    println!("Example 1: Simple Mathematical Sequence");
    println!("======================================");
    
    simple_mathematical_sequence().await?;

    // Example 2: Complex financial calculation
    println!("\nExample 2: Complex Financial Calculation");
    println!("=======================================");
    
    complex_financial_calculation().await?;

    // Example 3: Dynamic planning with different scenarios
    println!("\nExample 3: Dynamic Planning Scenarios");
    println!("===================================");
    
    dynamic_planning_scenarios().await?;

    println!("\n✅ Sequential Planner examples completed!");

    Ok(())
}

/// Example 1: Simple mathematical sequence
async fn simple_mathematical_sequence() -> Result<()> {
    let mut calculator = Calculator::new();
    
    // Goal: Calculate (5 + 3) * 2 and format as currency
    let plan = SequentialComputationPlan::new(
        "Simple Math Sequence",
        "Calculate (5 + 3) * 2 step by step"
    )
    .add_step(
        ComputationStep::new("AddNumbers", "Add 5 and 3", "add")
            .with_parameter("a", 5.0)
            .with_parameter("b", 3.0)
    )
    .add_step(
        ComputationStep::new("MultiplyResult", "Multiply result by 2", "multiply")
            .with_parameter("a", 8.0) // We would normally use the previous result
            .with_parameter("b", 2.0)
    );
    
    let result = plan.execute(&mut calculator).await?;
    let formatted = calculator.format_currency(result);
    
    println!("\n🎉 Final result: {}", formatted);
    println!("💾 Calculator memory: {}", calculator.get_memory());
    
    Ok(())
}

/// Example 2: Complex financial calculation
async fn complex_financial_calculation() -> Result<()> {
    let mut calculator = Calculator::new();
    
    // Goal: Calculate compound interest for multiple investments and combine
    let investment1_plan = SequentialComputationPlan::new(
        "Investment Portfolio Analysis",
        "Calculate compound interest for multiple investment scenarios"
    )
    .add_step(
        ComputationStep::new("Investment1", "Calculate first investment compound interest", "compound_interest")
            .with_parameter("principal", 1000.0)
            .with_parameter("rate", 0.05)
            .with_parameter("time", 3.0)
    );
    
    let result1 = investment1_plan.execute(&mut calculator).await?;
    
    let investment2_plan = SequentialComputationPlan::new(
        "Second Investment",
        "Calculate second investment compound interest"
    )
    .add_step(
        ComputationStep::new("Investment2", "Calculate second investment compound interest", "compound_interest")
            .with_parameter("principal", 2000.0)
            .with_parameter("rate", 0.04)
            .with_parameter("time", 5.0)
    );
    
    let result2 = investment2_plan.execute(&mut calculator).await?;
    
    // Combine results
    let total_plan = SequentialComputationPlan::new(
        "Combine Investments",
        "Add both investment results together"
    )
    .add_step(
        ComputationStep::new("CombineResults", "Add both investment results", "add")
            .with_parameter("a", result1)
            .with_parameter("b", result2)
    );
    
    let total_result = total_plan.execute(&mut calculator).await?;
    let formatted = calculator.format_currency(total_result);
    
    println!("\n💰 Total investment value: {}", formatted);
    
    Ok(())
}

/// Example 3: Dynamic planning with different scenarios
async fn dynamic_planning_scenarios() -> Result<()> {
    let scenarios = vec![
        ("Quick Calculation", vec![("add", 15.0, 25.0), ("multiply", 0.0, 3.0)]),
        ("Investment Analysis", vec![("compound_interest", 5000.0, 0.035), ("add", 0.0, 1000.0)]),
        ("Simple Arithmetic", vec![("add", 100.0, 200.0), ("multiply", 0.0, 1.5)]),
    ];
    
    for (scenario_name, operations) in scenarios {
        println!("\n--- Scenario: {} ---", scenario_name);
        
        let mut calculator = Calculator::new();
        let mut plan = SequentialComputationPlan::new(
            format!("Dynamic Plan: {}", scenario_name),
            format!("Automatically generated plan for {}", scenario_name)
        );
        
        for (i, (operation, param1, param2)) in operations.iter().enumerate() {
            let step = match *operation {
                "add" => ComputationStep::new(
                    format!("Step{}", i + 1),
                    format!("Perform {} operation", operation),
                    *operation
                )
                .with_parameter("a", *param1)
                .with_parameter("b", *param2),
                "multiply" => {
                    let a_val = if *param1 == 0.0 { calculator.get_memory() } else { *param1 };
                    ComputationStep::new(
                        format!("Step{}", i + 1),
                        format!("Perform {} operation", operation),
                        *operation
                    )
                    .with_parameter("a", a_val)
                    .with_parameter("b", *param2)
                },
                "compound_interest" => ComputationStep::new(
                    format!("Step{}", i + 1),
                    format!("Perform {} calculation", operation),
                    *operation
                )
                .with_parameter("principal", *param1)
                .with_parameter("rate", *param2)
                .with_parameter("time", 10.0), // Fixed time for demo
                _ => continue,
            };
            
            plan = plan.add_step(step);
        }
        
        let start_time = std::time::Instant::now();
        let result = plan.execute(&mut calculator).await?;
        let execution_time = start_time.elapsed();
        
        println!("✅ Scenario result: {:.2}", result);
        println!("⏱️  Execution time: {:?}", execution_time);
    }
    
    println!("\n🎉 All dynamic planning scenarios completed!");
    
    Ok(())
}