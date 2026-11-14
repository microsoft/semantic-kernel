//! Food Preparation Workflow Example
//! 
//! This example demonstrates a sophisticated multi-stage workflow for restaurant
//! food preparation. It showcases:
//! - Complex workflow orchestration with parallel and sequential steps
//! - Resource management and constraint handling (staff, equipment, ingredients)
//! - Dynamic routing based on order complexity and kitchen capacity
//! - Quality control checkpoints and retry mechanisms
//! - Real-time status updates and kitchen coordination
//! - Integration with inventory management and customer notifications

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_process::{
    ProcessStep, ProcessContext, ProcessResult, StepResult, ProcessEngine, 
    WorkflowProcess, Process
};
use async_trait::async_trait;
use std::sync::Arc;
use serde::{Deserialize, Serialize};
use std::time::Duration;

/// Order information for food preparation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FoodOrder {
    pub order_id: String,
    pub customer_name: String,
    pub items: Vec<OrderItem>,
    pub special_instructions: Option<String>,
    pub priority: OrderPriority,
    pub estimated_prep_time: u32, // minutes
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderItem {
    pub name: String,
    pub quantity: u32,
    pub complexity: ItemComplexity,
    pub ingredients: Vec<String>,
    pub allergens: Vec<String>,
    pub cooking_method: String,
    pub prep_time: u32, // minutes
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderPriority {
    Standard,
    Expedite,
    VIP,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
pub enum ItemComplexity {
    Simple,    // Salads, cold items
    Medium,    // Grilled items, simple cooking
    Complex,   // Multi-step preparation, sauces
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KitchenStatus {
    pub available_stations: Vec<String>,
    pub busy_stations: Vec<String>,
    pub available_staff: u32,
    pub current_orders: u32,
    pub average_wait_time: u32,
}

/// Step 1: Validate order and check inventory
#[derive(Debug, Clone)]
pub struct ValidateOrderStep;

#[async_trait]
impl ProcessStep for ValidateOrderStep {
    fn name(&self) -> &str {
        "ValidateOrder"
    }
    
    fn description(&self) -> &str {
        "Validate order items and check ingredient availability"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("📋 Validating order and checking inventory...");
        
        let order: FoodOrder = context.get_state("food_order")?.unwrap();
        
        let mut validation_issues = Vec::new();
        let mut missing_ingredients = Vec::new();
        
        // Simulate inventory check
        for item in &order.items {
            println!("   🔍 Checking: {} x{}", item.name, item.quantity);
            
            for ingredient in &item.ingredients {
                // Simulate random inventory issues
                if rand::random::<f32>() < 0.1 {
                    missing_ingredients.push(format!("{} for {}", ingredient, item.name));
                }
            }
            
            // Check for special dietary requirements
            if !item.allergens.is_empty() {
                println!("     ⚠️  Allergen alert: {:?}", item.allergens);
            }
        }
        
        // Simulate validation rules
        if order.items.len() > 10 {
            validation_issues.push("Large order - requires manager approval".to_string());
        }
        
        let validation_passed = validation_issues.is_empty() && missing_ingredients.is_empty();
        
        if validation_passed {
            println!("   ✅ Order validation passed");
            context.set_state("validation_passed", true)?;
        } else {
            println!("   ❌ Validation issues found:");
            for issue in &validation_issues {
                println!("     • {}", issue);
            }
            for ingredient in &missing_ingredients {
                println!("     • Missing: {}", ingredient);
            }
            context.set_state("validation_passed", false)?;
            context.set_state("validation_issues", validation_issues)?;
            context.set_state("missing_ingredients", missing_ingredients)?;
        }
        
        Ok(StepResult::success())
    }
}

/// Step 2: Assign kitchen stations and staff
#[derive(Debug, Clone)]
pub struct AssignKitchenResourcesStep;

#[async_trait]
impl ProcessStep for AssignKitchenResourcesStep {
    fn name(&self) -> &str {
        "AssignKitchenResources"
    }
    
    fn description(&self) -> &str {
        "Assign appropriate kitchen stations and staff based on order complexity"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("👨‍🍳 Assigning kitchen resources...");
        
        let order: FoodOrder = context.get_state("food_order")?.unwrap();
        let validation_passed: bool = context.get_state("validation_passed")?.unwrap_or(false);
        
        if !validation_passed {
            println!("   ⏩ Skipping resource assignment - validation failed");
            return Ok(StepResult::success());
        }
        
        // Simulate kitchen status
        let kitchen_status = KitchenStatus {
            available_stations: vec![
                "Grill".to_string(),
                "Saute".to_string(), 
                "Cold_Station".to_string(),
                "Fryer".to_string(),
                "Oven".to_string(),
            ],
            busy_stations: vec!["Pastry".to_string()],
            available_staff: 4,
            current_orders: 3,
            average_wait_time: 15,
        };
        
        let mut assigned_stations = Vec::new();
        let mut assigned_staff = Vec::new();
        let mut estimated_total_time = 0u32;
        
        // Assign stations based on items
        for item in &order.items {
            let station = match item.cooking_method.as_str() {
                "grilled" => "Grill",
                "sauteed" => "Saute", 
                "fried" => "Fryer",
                "baked" => "Oven",
                "raw" | "cold" => "Cold_Station",
                _ => "Prep_Station",
            };
            
            if kitchen_status.available_stations.contains(&station.to_string()) {
                assigned_stations.push(station.to_string());
                println!("   🏠 {} → {} station", item.name, station);
            } else {
                println!("   ⏳ {} → {} station (waiting)", item.name, station);
            }
            
            estimated_total_time = estimated_total_time.max(item.prep_time);
        }
        
        // Assign staff based on complexity
        let required_staff = match order.items.iter().map(|i| &i.complexity).max() {
            Some(ItemComplexity::Complex) => 2,
            Some(ItemComplexity::Medium) => 1,
            _ => 1,
        };
        
        for i in 0..required_staff {
            assigned_staff.push(format!("Chef_{}", i + 1));
        }
        
        println!("   👥 Assigned staff: {:?}", assigned_staff);
        println!("   🕐 Estimated prep time: {} minutes", estimated_total_time);
        
        context.set_state("assigned_stations", assigned_stations)?;
        context.set_state("assigned_staff", assigned_staff)?;
        context.set_state("estimated_prep_time", estimated_total_time)?;
        context.set_state("kitchen_status", kitchen_status)?;
        
        Ok(StepResult::success())
    }
}

/// Step 3: Start food preparation (parallel processing simulation)
#[derive(Debug, Clone)]
pub struct StartPreparationStep;

#[async_trait]
impl ProcessStep for StartPreparationStep {
    fn name(&self) -> &str {
        "StartPreparation"
    }
    
    fn description(&self) -> &str {
        "Begin food preparation with parallel cooking processes"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🔥 Starting food preparation...");
        
        let order: FoodOrder = context.get_state("food_order")?.unwrap();
        let validation_passed: bool = context.get_state("validation_passed")?.unwrap_or(false);
        
        if !validation_passed {
            return Ok(StepResult::failure("Cannot start preparation - validation failed"));
        }
        
        let mut prep_results = Vec::new();
        
        // Simulate parallel preparation of different items
        for (_index, item) in order.items.iter().enumerate() {
            println!("   🍳 Starting: {} ({})", item.name, item.cooking_method);
            
            // Simulate preparation time (shortened for demo)
            let prep_delay = Duration::from_millis((item.prep_time * 10) as u64); // Scale down for demo
            tokio::time::sleep(prep_delay).await;
            
            // Simulate success/failure based on complexity
            let success_rate = match item.complexity {
                ItemComplexity::Simple => 0.95,
                ItemComplexity::Medium => 0.90,
                ItemComplexity::Complex => 0.85,
            };
            
            let success = rand::random::<f32>() < success_rate;
            
            if success {
                println!("     ✅ {} completed successfully", item.name);
                prep_results.push(format!("{}: SUCCESS", item.name));
            } else {
                println!("     ❌ {} requires rework", item.name);
                prep_results.push(format!("{}: REWORK_NEEDED", item.name));
            }
        }
        
        let all_success = prep_results.iter().all(|r| r.contains("SUCCESS"));
        
        context.set_state("prep_results", prep_results)?;
        context.set_state("all_items_ready", all_success)?;
        
        if all_success {
            println!("   🎉 All items prepared successfully!");
        } else {
            println!("   ⚠️  Some items need rework");
        }
        
        Ok(StepResult::success())
    }
}

/// Step 4: Quality control check
#[derive(Debug, Clone)]
pub struct QualityControlStep;

#[async_trait]
impl ProcessStep for QualityControlStep {
    fn name(&self) -> &str {
        "QualityControl"
    }
    
    fn description(&self) -> &str {
        "Perform quality control check on prepared items"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🔍 Performing quality control check...");
        
        let all_items_ready: bool = context.get_state("all_items_ready")?.unwrap_or(false);
        let prep_results: Vec<String> = context.get_state("prep_results")?.unwrap_or_default();
        
        if !all_items_ready {
            println!("   ⏳ Quality check postponed - items need rework");
            context.set_state("quality_check_result", "POSTPONED")?;
            return Ok(StepResult::success());
        }
        
        // Simulate quality checks
        let mut quality_issues = Vec::new();
        
        for result in &prep_results {
            if result.contains("SUCCESS") {
                let item_name = result.split(':').next().unwrap();
                
                // Simulate quality checks
                let checks = vec!["Temperature", "Presentation", "Taste", "Portion"];
                for check in checks {
                    if rand::random::<f32>() < 0.05 { // 5% chance of quality issue
                        quality_issues.push(format!("{} - {} issue", item_name, check));
                    }
                }
            }
        }
        
        let quality_passed = quality_issues.is_empty();
        
        if quality_passed {
            println!("   ✅ Quality control passed - all items meet standards");
            context.set_state("quality_check_result", "PASSED")?;
        } else {
            println!("   ⚠️  Quality issues detected:");
            for issue in &quality_issues {
                println!("     • {}", issue);
            }
            context.set_state("quality_check_result", "FAILED")?;
            context.set_state("quality_issues", quality_issues)?;
        }
        
        Ok(StepResult::success())
    }
}

/// Step 5: Plate and present order
#[derive(Debug, Clone)]
pub struct PlateAndPresentStep;

#[async_trait]
impl ProcessStep for PlateAndPresentStep {
    fn name(&self) -> &str {
        "PlateAndPresent"
    }
    
    fn description(&self) -> &str {
        "Final plating and presentation of the order"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🍽️  Final plating and presentation...");
        
        let quality_result: String = context.get_state("quality_check_result")?.unwrap_or_default();
        let order: FoodOrder = context.get_state("food_order")?.unwrap();
        
        match quality_result.as_str() {
            "PASSED" => {
                println!("   🎨 Plating {} items for order {}", order.items.len(), order.order_id);
                
                // Simulate plating time
                tokio::time::sleep(Duration::from_millis(200)).await;
                
                for item in &order.items {
                    println!("     🍴 {} plated with {} presentation", item.name, 
                             match item.complexity {
                                 ItemComplexity::Complex => "elaborate",
                                 ItemComplexity::Medium => "standard",
                                 ItemComplexity::Simple => "simple",
                             });
                }
                
                println!("   ✅ Order {} ready for service!", order.order_id);
                context.set_state("order_ready", true)?;
                context.set_state("completion_time", chrono::Utc::now().to_rfc3339())?;
                
                Ok(StepResult::success())
            }
            "FAILED" => {
                println!("   ❌ Cannot plate order - quality issues must be resolved first");
                Ok(StepResult::failure("Quality control failed"))
            }
            "POSTPONED" => {
                println!("   ⏳ Plating postponed - waiting for item completion");
                Ok(StepResult::failure("Items not ready for plating"))
            }
            _ => {
                println!("   ❓ Unknown quality status - cannot proceed");
                Ok(StepResult::failure("Unknown quality status"))
            }
        }
    }
}

/// Step 6: Notify customer and update order status
#[derive(Debug, Clone)]
pub struct NotifyCustomerStep;

#[async_trait]
impl ProcessStep for NotifyCustomerStep {
    fn name(&self) -> &str {
        "NotifyCustomer"
    }
    
    fn description(&self) -> &str {
        "Send notification to customer that order is ready"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("📱 Notifying customer...");
        
        let order: FoodOrder = context.get_state("food_order")?.unwrap();
        let order_ready: bool = context.get_state("order_ready")?.unwrap_or(false);
        
        if !order_ready {
            return Ok(StepResult::failure("Order not ready for customer notification"));
        }
        
        // Simulate notification delay
        tokio::time::sleep(Duration::from_millis(100)).await;
        
        let notification_methods = match order.priority {
            OrderPriority::VIP => vec!["SMS", "App Push", "Phone Call"],
            OrderPriority::Expedite => vec!["SMS", "App Push"],
            OrderPriority::Standard => vec!["App Push"],
        };
        
        println!("   📲 Sending notifications via: {:?}", notification_methods);
        println!("   📧 \"Hello {}, your order {} is ready for pickup!\"", 
                 order.customer_name, order.order_id);
        
        context.set_state("customer_notified", true)?;
        context.set_state("notification_methods", notification_methods)?;
        context.set_state("notification_sent_at", chrono::Utc::now().to_rfc3339())?;
        
        println!("   ✅ Customer notification sent successfully");
        
        Ok(StepResult::success())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("🍳 Semantic Kernel Rust - Food Preparation Workflow");
    println!("==================================================\n");

    // Example 1: Simple order workflow
    println!("Example 1: Simple Order Workflow");
    println!("===============================");
    
    simple_order_workflow().await?;

    // Example 2: Complex order with quality issues
    println!("\nExample 2: Complex Order with Challenges");
    println!("=======================================");
    
    complex_order_workflow().await?;

    // Example 3: VIP order with expedited processing
    println!("\nExample 3: VIP Order with Expedited Processing");
    println!("==============================================");
    
    vip_order_workflow().await?;

    println!("\n✅ Food Preparation Workflow examples completed!");

    Ok(())
}

/// Example of a simple order workflow
async fn simple_order_workflow() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    let order = FoodOrder {
        order_id: "ORD-001".to_string(),
        customer_name: "Alice Johnson".to_string(),
        priority: OrderPriority::Standard,
        estimated_prep_time: 15,
        items: vec![
            OrderItem {
                name: "Caesar Salad".to_string(),
                quantity: 1,
                complexity: ItemComplexity::Simple,
                ingredients: vec!["Lettuce".to_string(), "Croutons".to_string(), "Parmesan".to_string()],
                allergens: vec!["Dairy".to_string()],
                cooking_method: "cold".to_string(),
                prep_time: 5,
            },
            OrderItem {
                name: "Grilled Chicken".to_string(),
                quantity: 1,
                complexity: ItemComplexity::Medium,
                ingredients: vec!["Chicken Breast".to_string(), "Herbs".to_string(), "Oil".to_string()],
                allergens: vec![],
                cooking_method: "grilled".to_string(),
                prep_time: 12,
            },
        ],
        special_instructions: Some("No croutons, extra dressing".to_string()),
    };
    
    let process = create_food_preparation_process();
    let result = execute_food_order(process, order, &kernel, &process_engine).await?;
    
    if let Some(ready) = result.get_state::<bool>("order_ready")? {
        if ready {
            println!("🎉 Simple order completed successfully!");
        }
    }
    
    Ok(())
}

/// Example of a complex order with potential quality issues
async fn complex_order_workflow() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    let order = FoodOrder {
        order_id: "ORD-002".to_string(),
        customer_name: "Bob Martinez".to_string(),
        priority: OrderPriority::Standard,
        estimated_prep_time: 25,
        items: vec![
            OrderItem {
                name: "Beef Wellington".to_string(),
                quantity: 1,
                complexity: ItemComplexity::Complex,
                ingredients: vec!["Beef Tenderloin".to_string(), "Puff Pastry".to_string(), "Mushrooms".to_string()],
                allergens: vec!["Gluten".to_string()],
                cooking_method: "baked".to_string(),
                prep_time: 25,
            },
            OrderItem {
                name: "Lobster Bisque".to_string(),
                quantity: 1,
                complexity: ItemComplexity::Complex,
                ingredients: vec!["Lobster".to_string(), "Cream".to_string(), "Cognac".to_string()],
                allergens: vec!["Shellfish".to_string(), "Dairy".to_string()],
                cooking_method: "sauteed".to_string(),
                prep_time: 20,
            },
        ],
        special_instructions: Some("Medium-rare, extra sauce on side".to_string()),
    };
    
    let process = create_food_preparation_process();
    
    match execute_food_order(process, order, &kernel, &process_engine).await {
        Ok(result) => {
            if let Some(ready) = result.get_state::<bool>("order_ready")? {
                if ready {
                    println!("🎉 Complex order completed successfully!");
                } else {
                    println!("⚠️  Complex order completed with issues");
                }
            }
        }
        Err(e) => {
            println!("❌ Complex order workflow failed: {}", e);
            println!("   This demonstrates error handling in complex workflows");
        }
    }
    
    Ok(())
}

/// Example of VIP order with expedited processing
async fn vip_order_workflow() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    let order = FoodOrder {
        order_id: "VIP-003".to_string(),
        customer_name: "Dr. Sarah Chen".to_string(),
        priority: OrderPriority::VIP,
        estimated_prep_time: 18,
        items: vec![
            OrderItem {
                name: "Pan-Seared Salmon".to_string(),
                quantity: 1,
                complexity: ItemComplexity::Medium,
                ingredients: vec!["Salmon Fillet".to_string(), "Lemon".to_string(), "Capers".to_string()],
                allergens: vec!["Fish".to_string()],
                cooking_method: "sauteed".to_string(),
                prep_time: 15,
            },
            OrderItem {
                name: "Truffle Risotto".to_string(),
                quantity: 1,
                complexity: ItemComplexity::Complex,
                ingredients: vec!["Arborio Rice".to_string(), "Truffle Oil".to_string(), "Parmesan".to_string()],
                allergens: vec!["Dairy".to_string()],
                cooking_method: "sauteed".to_string(),
                prep_time: 18,
            },
        ],
        special_instructions: Some("VIP customer - priority preparation".to_string()),
    };
    
    let process = create_food_preparation_process();
    let result = execute_food_order(process, order, &kernel, &process_engine).await?;
    
    if let Some(ready) = result.get_state::<bool>("order_ready")? {
        if ready {
            println!("🌟 VIP order completed with premium service!");
            if let Some(methods) = result.get_state::<Vec<String>>("notification_methods")? {
                println!("   📱 VIP notifications sent via: {:?}", methods);
            }
        }
    }
    
    Ok(())
}

/// Create the food preparation process workflow
fn create_food_preparation_process() -> Arc<WorkflowProcess> {
    Arc::new(
        WorkflowProcess::new("FoodPreparationWorkflow", "Complete restaurant food preparation process")
            .add_step(Arc::new(ValidateOrderStep))
            .add_step(Arc::new(AssignKitchenResourcesStep))
            .add_step(Arc::new(StartPreparationStep))
            .add_step(Arc::new(QualityControlStep))
            .add_step(Arc::new(PlateAndPresentStep))
            .add_step(Arc::new(NotifyCustomerStep))
    )
}

/// Execute a food order through the preparation workflow
async fn execute_food_order(
    process: Arc<WorkflowProcess>,
    order: FoodOrder,
    kernel: &Kernel,
    engine: &ProcessEngine,
) -> Result<sk_process::ProcessContext> {
    let mut context = sk_process::ProcessContext::new(uuid::Uuid::new_v4());
    context.set_state("food_order", order)?;
    
    // Execute the process step by step with proper error handling
    let steps = process.steps();
    
    for (step_index, step) in steps.iter().enumerate() {
        context.current_step = step_index;
        
        match step.execute(&mut context, kernel).await {
            Ok(result) => {
                if !result.success {
                    // Some steps are allowed to fail and continue (like quality issues)
                    if step.name() == "PlateAndPresent" || step.name() == "NotifyCustomer" {
                        return Err(anyhow::anyhow!("Step '{}' failed: {}", 
                            step.name(), 
                            result.error.unwrap_or_else(|| "Unknown error".to_string())
                        ));
                    }
                    // For other steps, log but continue
                    println!("   ⚠️  Step '{}' had issues but workflow continues", step.name());
                }
                
                if result.pause_process {
                    println!("   ⏸️  Process paused after step: {}", step.name());
                    break;
                }
            }
            Err(e) => {
                return Err(anyhow::anyhow!("Step '{}' execution failed: {}", step.name(), e));
            }
        }
    }
    
    Ok(context)
}