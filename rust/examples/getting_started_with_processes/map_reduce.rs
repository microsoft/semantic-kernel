//! Map-Reduce Parallel Processing Example
//! 
//! This example demonstrates sophisticated parallel processing patterns using
//! the process framework. It showcases:
//! - Map-Reduce computational patterns with parallel execution
//! - Dynamic work distribution across multiple processing units
//! - Result aggregation and error handling in distributed scenarios
//! - Load balancing and resource optimization strategies
//! - Fault tolerance and retry mechanisms for failed tasks
//! - Performance monitoring and scaling based on workload

use anyhow::Result;
use semantic_kernel::{Kernel, KernelBuilder};
use sk_process::{
    ProcessStep, ProcessContext, ProcessResult, StepResult, ProcessEngine, 
    WorkflowProcess, Process
};
use async_trait::async_trait;
use std::sync::Arc;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};
use std::collections::HashMap;

/// Configuration for map-reduce job
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MapReduceJob {
    pub job_id: String,
    pub job_name: String,
    pub input_data: Vec<DataChunk>,
    pub map_function: String,
    pub reduce_function: String,
    pub parallelism_level: usize,
    pub timeout_seconds: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DataChunk {
    pub chunk_id: String,
    pub data: Vec<i32>, // Simplified data for demo
    pub size: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MapResult {
    pub chunk_id: String,
    pub processed_data: Vec<i32>,
    pub processing_time_ms: u64,
    pub success: bool,
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReduceResult {
    pub final_result: i32,
    pub total_processing_time_ms: u64,
    pub chunks_processed: usize,
    pub errors_encountered: usize,
}

/// Step 1: Initialize and validate map-reduce job
#[derive(Debug, Clone)]
pub struct InitializeJobStep;

#[async_trait]
impl ProcessStep for InitializeJobStep {
    fn name(&self) -> &str {
        "InitializeJob"
    }
    
    fn description(&self) -> &str {
        "Initialize map-reduce job and validate input parameters"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🚀 Initializing Map-Reduce job...");
        
        let job: MapReduceJob = context.get_state("mapreduce_job")?.unwrap();
        
        println!("   📋 Job: {} ({})", job.job_name, job.job_id);
        println!("   📊 Input chunks: {}", job.input_data.len());
        println!("   ⚡ Parallelism level: {}", job.parallelism_level);
        println!("   ⏱️  Timeout: {} seconds", job.timeout_seconds);
        
        // Validate job parameters
        let mut validation_errors = Vec::new();
        
        if job.input_data.is_empty() {
            validation_errors.push("No input data chunks provided".to_string());
        }
        
        if job.parallelism_level == 0 {
            validation_errors.push("Parallelism level must be greater than 0".to_string());
        }
        
        if job.parallelism_level > 16 {
            validation_errors.push("Parallelism level too high (max 16)".to_string());
        }
        
        let total_data_size: usize = job.input_data.iter().map(|chunk| chunk.size).sum();
        println!("   💾 Total data size: {} elements", total_data_size);
        
        if validation_errors.is_empty() {
            println!("   ✅ Job validation passed");
            context.set_state("job_validated", true)?;
            context.set_state("total_data_size", total_data_size)?;
            context.set_state("start_time", chrono::Utc::now())?;
        } else {
            println!("   ❌ Job validation failed:");
            for error in &validation_errors {
                println!("     • {}", error);
            }
            context.set_state("job_validated", false)?;
            context.set_state("validation_errors", validation_errors)?;
        }
        
        Ok(StepResult::success())
    }
}

/// Step 2: Distribute work across parallel map workers
#[derive(Debug, Clone)]
pub struct MapPhaseStep;

#[async_trait]
impl ProcessStep for MapPhaseStep {
    fn name(&self) -> &str {
        "MapPhase"
    }
    
    fn description(&self) -> &str {
        "Execute map phase with parallel processing of data chunks"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🗺️  Executing Map Phase...");
        
        let job_validated: bool = context.get_state("job_validated")?.unwrap_or(false);
        if !job_validated {
            return Ok(StepResult::failure("Job not validated - cannot execute map phase"));
        }
        
        let job: MapReduceJob = context.get_state("mapreduce_job")?.unwrap();
        let start_time: chrono::DateTime<chrono::Utc> = context.get_state("start_time")?.unwrap();
        
        println!("   👷 Starting {} parallel workers", job.parallelism_level);
        
        // Simulate parallel processing with chunked execution
        let chunks_per_worker = (job.input_data.len() + job.parallelism_level - 1) / job.parallelism_level;
        let mut map_results = Vec::new();
        let mut worker_tasks = Vec::new();
        
        for worker_id in 0..job.parallelism_level {
            let start_idx = worker_id * chunks_per_worker;
            let end_idx = ((worker_id + 1) * chunks_per_worker).min(job.input_data.len());
            
            if start_idx >= job.input_data.len() {
                break;
            }
            
            let worker_chunks: Vec<DataChunk> = job.input_data[start_idx..end_idx].to_vec();
            let map_function = job.map_function.clone();
            
            println!("     🔧 Worker {} processing chunks {} to {}", worker_id, start_idx, end_idx - 1);
            
            // Simulate async worker execution
            let worker_future = async move {
                let mut worker_results = Vec::new();
                
                for chunk in worker_chunks {
                    let processing_start = Instant::now();
                    
                    // Simulate map operation based on function type
                    let processed_data = match map_function.as_str() {
                        "square" => chunk.data.iter().map(|x| x * x).collect(),
                        "double" => chunk.data.iter().map(|x| x * 2).collect(),
                        "increment" => chunk.data.iter().map(|x| x + 1).collect(),
                        "filter_even" => chunk.data.iter().filter(|x| *x % 2 == 0).cloned().collect(),
                        _ => chunk.data.clone(),
                    };
                    
                    // Simulate processing time
                    let processing_delay = Duration::from_millis(10 + (chunk.size as u64 * 2));
                    tokio::time::sleep(processing_delay).await;
                    
                    // Simulate occasional failures
                    let success = rand::random::<f32>() > 0.05; // 5% failure rate
                    
                    let result = MapResult {
                        chunk_id: chunk.chunk_id.clone(),
                        processed_data: if success { processed_data } else { Vec::new() },
                        processing_time_ms: processing_start.elapsed().as_millis() as u64,
                        success,
                        error_message: if success { None } else { Some("Simulated processing error".to_string()) },
                    };
                    
                    if success {
                        println!("       ✅ Chunk {} processed ({} elements)", chunk.chunk_id, result.processed_data.len());
                    } else {
                        println!("       ❌ Chunk {} failed", chunk.chunk_id);
                    }
                    
                    worker_results.push(result);
                }
                
                worker_results
            };
            
            worker_tasks.push(worker_future);
        }
        
        // Execute all workers in parallel (simulated with sequential execution for demo)
        for worker_future in worker_tasks {
            let worker_results = worker_future.await;
            map_results.extend(worker_results);
        }
        
        let map_phase_time = chrono::Utc::now().signed_duration_since(start_time);
        let successful_chunks = map_results.iter().filter(|r| r.success).count();
        let failed_chunks = map_results.len() - successful_chunks;
        
        println!("   📊 Map phase completed:");
        println!("     ✅ Successful chunks: {}", successful_chunks);
        println!("     ❌ Failed chunks: {}", failed_chunks);
        println!("     ⏱️  Phase time: {:?}", map_phase_time);
        
        context.set_state("map_results", map_results)?;
        context.set_state("map_phase_time", map_phase_time.num_milliseconds() as u64)?;
        context.set_state("successful_chunks", successful_chunks)?;
        context.set_state("failed_chunks", failed_chunks)?;
        
        if successful_chunks == 0 {
            Ok(StepResult::failure("All map operations failed"))
        } else {
            Ok(StepResult::success())
        }
    }
}

/// Step 3: Handle failed chunks with retry mechanism
#[derive(Debug, Clone)]
pub struct RetryFailedChunksStep;

#[async_trait]
impl ProcessStep for RetryFailedChunksStep {
    fn name(&self) -> &str {
        "RetryFailedChunks"
    }
    
    fn description(&self) -> &str {
        "Retry processing of failed chunks with error recovery"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("🔄 Retrying failed chunks...");
        
        let map_results: Vec<MapResult> = context.get_state("map_results")?.unwrap();
        let failed_chunks: usize = context.get_state("failed_chunks")?.unwrap_or(0);
        
        if failed_chunks == 0 {
            println!("   ⏩ No failed chunks to retry");
            return Ok(StepResult::success());
        }
        
        let job: MapReduceJob = context.get_state("mapreduce_job")?.unwrap();
        let mut updated_results = map_results.clone();
        let mut retry_count = 0;
        
        println!("   🔧 Retrying {} failed chunks", failed_chunks);
        
        for result in &mut updated_results {
            if !result.success {
                println!("     🔄 Retrying chunk: {}", result.chunk_id);
                
                // Find original chunk data
                if let Some(original_chunk) = job.input_data.iter().find(|c| c.chunk_id == result.chunk_id) {
                    // Simulate retry with higher success rate
                    let retry_success = rand::random::<f32>() > 0.02; // 2% failure rate on retry
                    
                    if retry_success {
                        let processed_data = match job.map_function.as_str() {
                            "square" => original_chunk.data.iter().map(|x| x * x).collect(),
                            "double" => original_chunk.data.iter().map(|x| x * 2).collect(),
                            "increment" => original_chunk.data.iter().map(|x| x + 1).collect(),
                            "filter_even" => original_chunk.data.iter().filter(|x| *x % 2 == 0).cloned().collect(),
                            _ => original_chunk.data.clone(),
                        };
                        
                        result.processed_data = processed_data;
                        result.success = true;
                        result.error_message = None;
                        retry_count += 1;
                        
                        println!("       ✅ Retry successful for chunk {}", result.chunk_id);
                    } else {
                        println!("       ❌ Retry failed for chunk {}", result.chunk_id);
                    }
                }
                
                // Simulate retry delay
                tokio::time::sleep(Duration::from_millis(50)).await;
            }
        }
        
        let final_successful = updated_results.iter().filter(|r| r.success).count();
        let final_failed = updated_results.len() - final_successful;
        
        println!("   📊 Retry phase completed:");
        println!("     🔄 Chunks retried: {}", retry_count);
        println!("     ✅ Total successful: {}", final_successful);
        println!("     ❌ Still failed: {}", final_failed);
        
        context.set_state("map_results", updated_results)?;
        context.set_state("final_successful_chunks", final_successful)?;
        context.set_state("final_failed_chunks", final_failed)?;
        
        Ok(StepResult::success())
    }
}

/// Step 4: Reduce phase - aggregate all results
#[derive(Debug, Clone)]
pub struct ReducePhaseStep;

#[async_trait]
impl ProcessStep for ReducePhaseStep {
    fn name(&self) -> &str {
        "ReducePhase"
    }
    
    fn description(&self) -> &str {
        "Execute reduce phase to aggregate all map results"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("📊 Executing Reduce Phase...");
        
        let map_results: Vec<MapResult> = context.get_state("map_results")?.unwrap();
        let start_time: chrono::DateTime<chrono::Utc> = context.get_state("start_time")?.unwrap();
        let job: MapReduceJob = context.get_state("mapreduce_job")?.unwrap();
        
        let successful_results: Vec<&MapResult> = map_results.iter().filter(|r| r.success).collect();
        
        if successful_results.is_empty() {
            return Ok(StepResult::failure("No successful map results to reduce"));
        }
        
        println!("   🔢 Reducing {} successful results", successful_results.len());
        
        // Collect all processed data
        let mut all_data = Vec::new();
        for result in &successful_results {
            all_data.extend(&result.processed_data);
        }
        
        println!("   📊 Total elements to reduce: {}", all_data.len());
        
        // Simulate reduce operation based on function type
        let reduce_start = Instant::now();
        let final_result = match job.reduce_function.as_str() {
            "sum" => all_data.iter().sum(),
            "max" => *all_data.iter().max().unwrap_or(&0),
            "min" => *all_data.iter().min().unwrap_or(&0),
            "count" => all_data.len() as i32,
            "average" => if all_data.is_empty() { 0 } else { all_data.iter().sum::<i32>() / all_data.len() as i32 },
            _ => all_data.iter().sum(), // Default to sum
        };
        
        // Simulate reduce processing time
        let reduce_delay = Duration::from_millis(50 + (all_data.len() as u64 / 1000));
        tokio::time::sleep(reduce_delay).await;
        
        let reduce_time = reduce_start.elapsed();
        let total_time = chrono::Utc::now().signed_duration_since(start_time);
        
        let reduce_result = ReduceResult {
            final_result,
            total_processing_time_ms: total_time.num_milliseconds() as u64,
            chunks_processed: successful_results.len(),
            errors_encountered: map_results.len() - successful_results.len(),
        };
        
        println!("   🎯 Reduce operation: {} → {}", job.reduce_function, final_result);
        println!("   ⏱️  Reduce time: {:?}", reduce_time);
        println!("   ⏱️  Total time: {:?}", total_time);
        
        context.set_state("reduce_result", reduce_result)?;
        context.set_state("reduce_time", reduce_time.as_millis() as u64)?;
        context.set_state("total_time", total_time.num_milliseconds() as u64)?;
        
        Ok(StepResult::success())
    }
}

/// Step 5: Generate performance report
#[derive(Debug, Clone)]
pub struct GenerateReportStep;

#[async_trait]
impl ProcessStep for GenerateReportStep {
    fn name(&self) -> &str {
        "GenerateReport"
    }
    
    fn description(&self) -> &str {
        "Generate comprehensive performance and results report"
    }

    async fn execute(
        &self,
        context: &mut ProcessContext,
        _kernel: &Kernel,
    ) -> ProcessResult<StepResult> {
        println!("📈 Generating performance report...");
        
        let job: MapReduceJob = context.get_state("mapreduce_job")?.unwrap();
        let reduce_result: ReduceResult = context.get_state("reduce_result")?.unwrap();
        let map_results: Vec<MapResult> = context.get_state("map_results")?.unwrap();
        let total_data_size: usize = context.get_state("total_data_size")?.unwrap_or(0);
        
        // Calculate statistics
        let successful_map_times: Vec<u64> = map_results.iter()
            .filter(|r| r.success)
            .map(|r| r.processing_time_ms)
            .collect();
        
        let avg_map_time = if successful_map_times.is_empty() { 0 } 
            else { successful_map_times.iter().sum::<u64>() / successful_map_times.len() as u64 };
        
        let max_map_time = successful_map_times.iter().max().unwrap_or(&0);
        let min_map_time = successful_map_times.iter().min().unwrap_or(&0);
        
        let throughput = if reduce_result.total_processing_time_ms > 0 {
            (total_data_size as f64 * 1000.0) / reduce_result.total_processing_time_ms as f64
        } else { 0.0 };
        
        // Generate report
        let mut report = HashMap::new();
        report.insert("job_id".to_string(), job.job_id.clone());
        report.insert("job_name".to_string(), job.job_name.clone());
        report.insert("final_result".to_string(), reduce_result.final_result.to_string());
        report.insert("total_time_ms".to_string(), reduce_result.total_processing_time_ms.to_string());
        report.insert("chunks_processed".to_string(), reduce_result.chunks_processed.to_string());
        report.insert("errors_encountered".to_string(), reduce_result.errors_encountered.to_string());
        report.insert("throughput_elements_per_sec".to_string(), format!("{:.2}", throughput));
        report.insert("avg_map_time_ms".to_string(), avg_map_time.to_string());
        report.insert("max_map_time_ms".to_string(), max_map_time.to_string());
        report.insert("min_map_time_ms".to_string(), min_map_time.to_string());
        
        println!("\n   📋 === MAP-REDUCE JOB REPORT ===");
        println!("   🆔 Job: {} ({})", job.job_name, job.job_id);
        println!("   🎯 Final Result: {}", reduce_result.final_result);
        println!("   ⏱️  Total Time: {}ms", reduce_result.total_processing_time_ms);
        println!("   📊 Chunks Processed: {} / {}", reduce_result.chunks_processed, job.input_data.len());
        println!("   ❌ Errors: {}", reduce_result.errors_encountered);
        println!("   🚀 Throughput: {:.2} elements/sec", throughput);
        println!("   📈 Map Times - Avg: {}ms, Min: {}ms, Max: {}ms", avg_map_time, min_map_time, max_map_time);
        println!("   ⚡ Parallelism: {} workers", job.parallelism_level);
        println!("   🔧 Operations: {} → {}", job.map_function, job.reduce_function);
        
        context.set_state("performance_report", report)?;
        context.set_state("throughput", throughput)?;
        
        println!("   ✅ Performance report generated");
        
        Ok(StepResult::success())
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize environment and logging
    dotenv::dotenv().ok();
    tracing_subscriber::fmt::init();

    println!("⚡ Semantic Kernel Rust - Map-Reduce Parallel Processing");
    println!("=======================================================\n");

    // Example 1: Simple sum aggregation
    println!("Example 1: Parallel Sum Aggregation");
    println!("==================================");
    
    simple_sum_mapreduce().await?;

    // Example 2: Complex data transformation with filtering
    println!("\nExample 2: Data Transformation with Filtering");
    println!("============================================");
    
    complex_transformation_mapreduce().await?;

    // Example 3: High-throughput processing with error handling
    println!("\nExample 3: High-Throughput Processing with Error Handling");
    println!("========================================================");
    
    high_throughput_mapreduce().await?;

    println!("\n✅ Map-Reduce Parallel Processing examples completed!");

    Ok(())
}

/// Example 1: Simple sum aggregation
async fn simple_sum_mapreduce() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Create sample data chunks
    let data_chunks = vec![
        DataChunk {
            chunk_id: "chunk_1".to_string(),
            data: vec![1, 2, 3, 4, 5],
            size: 5,
        },
        DataChunk {
            chunk_id: "chunk_2".to_string(),
            data: vec![6, 7, 8, 9, 10],
            size: 5,
        },
        DataChunk {
            chunk_id: "chunk_3".to_string(),
            data: vec![11, 12, 13, 14, 15],
            size: 5,
        },
        DataChunk {
            chunk_id: "chunk_4".to_string(),
            data: vec![16, 17, 18, 19, 20],
            size: 5,
        },
    ];
    
    let job = MapReduceJob {
        job_id: "JOB-001".to_string(),
        job_name: "Simple Sum Aggregation".to_string(),
        input_data: data_chunks,
        map_function: "double".to_string(),  // Double each number
        reduce_function: "sum".to_string(),   // Sum all results
        parallelism_level: 2,
        timeout_seconds: 30,
    };
    
    let process = create_mapreduce_process();
    let result = execute_mapreduce_job(process, job, &kernel, &process_engine).await?;
    
    if let Some(final_result) = result.get_state::<ReduceResult>("reduce_result")? {
        println!("🎉 Simple sum completed! Final result: {}", final_result.final_result);
    }
    
    Ok(())
}

/// Example 2: Complex data transformation with filtering
async fn complex_transformation_mapreduce() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Create larger dataset with mixed values
    let data_chunks = vec![
        DataChunk {
            chunk_id: "data_A".to_string(),
            data: (1..=50).collect(),
            size: 50,
        },
        DataChunk {
            chunk_id: "data_B".to_string(),
            data: (51..=100).collect(),
            size: 50,
        },
        DataChunk {
            chunk_id: "data_C".to_string(),
            data: (101..=150).collect(),
            size: 50,
        },
    ];
    
    let job = MapReduceJob {
        job_id: "JOB-002".to_string(),
        job_name: "Filter Even Numbers and Find Maximum".to_string(),
        input_data: data_chunks,
        map_function: "filter_even".to_string(),  // Filter even numbers only
        reduce_function: "max".to_string(),       // Find maximum value
        parallelism_level: 3,
        timeout_seconds: 60,
    };
    
    let process = create_mapreduce_process();
    let result = execute_mapreduce_job(process, job, &kernel, &process_engine).await?;
    
    if let Some(final_result) = result.get_state::<ReduceResult>("reduce_result")? {
        println!("🎉 Complex transformation completed! Maximum even number: {}", final_result.final_result);
    }
    
    Ok(())
}

/// Example 3: High-throughput processing with error handling
async fn high_throughput_mapreduce() -> Result<()> {
    let kernel = KernelBuilder::new().build();
    let process_engine = ProcessEngine::new();
    
    // Create many small chunks to simulate high-throughput scenario
    let mut data_chunks = Vec::new();
    for i in 0..12 {
        data_chunks.push(DataChunk {
            chunk_id: format!("chunk_{:02}", i),
            data: ((i*10)..((i+1)*10)).collect(),
            size: 10,
        });
    }
    
    let job = MapReduceJob {
        job_id: "JOB-003".to_string(),
        job_name: "High-Throughput Square and Average".to_string(),
        input_data: data_chunks,
        map_function: "square".to_string(),     // Square each number
        reduce_function: "average".to_string(),  // Calculate average
        parallelism_level: 4,
        timeout_seconds: 120,
    };
    
    let process = create_mapreduce_process();
    let result = execute_mapreduce_job(process, job, &kernel, &process_engine).await?;
    
    if let Some(final_result) = result.get_state::<ReduceResult>("reduce_result")? {
        if let Some(throughput) = result.get_state::<f64>("throughput")? {
            println!("🚀 High-throughput processing completed!");
            println!("   Average of squared numbers: {}", final_result.final_result);
            println!("   Throughput: {:.2} elements/sec", throughput);
        }
    }
    
    Ok(())
}

/// Create the map-reduce process workflow
fn create_mapreduce_process() -> Arc<WorkflowProcess> {
    Arc::new(
        WorkflowProcess::new("MapReduceWorkflow", "Parallel map-reduce processing workflow")
            .add_step(Arc::new(InitializeJobStep))
            .add_step(Arc::new(MapPhaseStep))
            .add_step(Arc::new(RetryFailedChunksStep))
            .add_step(Arc::new(ReducePhaseStep))
            .add_step(Arc::new(GenerateReportStep))
    )
}

/// Execute a map-reduce job through the processing workflow
async fn execute_mapreduce_job(
    process: Arc<WorkflowProcess>,
    job: MapReduceJob,
    kernel: &Kernel,
    engine: &ProcessEngine,
) -> Result<sk_process::ProcessContext> {
    let mut context = sk_process::ProcessContext::new(uuid::Uuid::new_v4());
    context.set_state("mapreduce_job", job)?;
    
    // Execute the process step by step
    let steps = process.steps();
    
    for (step_index, step) in steps.iter().enumerate() {
        context.current_step = step_index;
        
        match step.execute(&mut context, kernel).await {
            Ok(result) => {
                if !result.success {
                    return Err(anyhow::anyhow!("Step '{}' failed: {}", 
                        step.name(), 
                        result.error.unwrap_or_else(|| "Unknown error".to_string())
                    ));
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