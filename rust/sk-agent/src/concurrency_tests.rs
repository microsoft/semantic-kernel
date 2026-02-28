//! Concurrency tests for the Agent Framework

use anyhow::Result;
use semantic_kernel::KernelBuilder;
use crate::{
    Agent, ChatCompletionAgent, AgentThread,
    orchestration::{SequentialOrchestration, Orchestration},
};
use std::sync::Arc;
use std::time::Duration;
use tokio::time::timeout;

/// Test that spawns 20 agents concurrently to verify no data races or deadlocks
#[tokio::test]
async fn test_concurrent_agents_no_deadlocks() -> Result<()> {
    const NUM_AGENTS: usize = 20;
    const TIMEOUT_DURATION: Duration = Duration::from_secs(30);
    
    // This test verifies that:
    // 1. Multiple agents can be created concurrently
    // 2. Multiple agents can process requests concurrently 
    // 3. No deadlocks occur during concurrent execution
    // 4. No data races occur in shared state
    
    let test_execution = async {
        // Create 20 agents concurrently
        let mut agent_handles = Vec::new();
        
        for i in 0..NUM_AGENTS {
            let handle = tokio::spawn(async move {
                let kernel = KernelBuilder::new().build();
                let agent = ChatCompletionAgent::builder()
                    .name(format!("ConcurrentAgent{}", i))
                    .description(format!("Test agent {} for concurrency", i))
                    .instructions("You are a test agent for concurrency testing.")
                    .kernel(kernel)
                    .build()?;
                
                Ok::<Arc<dyn Agent>, anyhow::Error>(Arc::new(agent))
            });
            agent_handles.push(handle);
        }
        
        // Wait for all agents to be created
        let mut agents = Vec::new();
        for handle in agent_handles {
            let agent = handle.await??;
            agents.push(agent);
        }
        
        assert_eq!(agents.len(), NUM_AGENTS);
        println!("Successfully created {} agents concurrently", NUM_AGENTS);
        
        // Test concurrent invocations
        let mut invocation_handles = Vec::new();
        
        for (i, agent) in agents.iter().enumerate() {
            let agent_clone = agent.clone();
            let handle = tokio::spawn(async move {
                let mut thread = AgentThread::new();
                let message = format!("Hello from concurrent test {}", i);
                
                // Each agent processes multiple messages
                let mut responses = Vec::new();
                for j in 0..3 {
                    let response = agent_clone.invoke_async(
                        &mut thread, 
                        &format!("{} - message {}", message, j)
                    ).await?;
                    responses.push(response);
                }
                
                Ok::<Vec<_>, anyhow::Error>(responses)
            });
            invocation_handles.push(handle);
        }
        
        // Wait for all concurrent invocations to complete
        let mut all_responses = Vec::new();
        for handle in invocation_handles {
            let responses = handle.await??;
            all_responses.extend(responses);
        }
        
        // Verify we got responses from all concurrent executions
        assert_eq!(all_responses.len(), NUM_AGENTS * 3);
        println!("Successfully processed {} concurrent agent invocations", all_responses.len());
        
        // Test concurrent orchestrations
        let orchestration_handles: Vec<_> = (0..5).map(|i| {
            let agents_subset = agents[i * 4..(i + 1) * 4].to_vec();
            tokio::spawn(async move {
                let orchestration = SequentialOrchestration::new(agents_subset);
                let result = orchestration.execute_async(
                    &format!("Orchestration test {}", i), 
                    None
                ).await?;
                Ok::<String, anyhow::Error>(result.output.content)
            })
        }).collect();
        
        // Wait for all orchestrations to complete
        let mut orchestration_results = Vec::new();
        for handle in orchestration_handles {
            let result = handle.await??;
            orchestration_results.push(result);
        }
        
        assert_eq!(orchestration_results.len(), 5);
        println!("Successfully completed {} concurrent orchestrations", orchestration_results.len());
        
        Ok::<(), anyhow::Error>(())
    };
    
    // Run the test with a timeout to catch potential deadlocks
    match timeout(TIMEOUT_DURATION, test_execution).await {
        Ok(Ok(())) => {
            println!("✅ Concurrency test passed: No deadlocks or data races detected");
            Ok(())
        }
        Ok(Err(e)) => {
            println!("❌ Concurrency test failed with error: {}", e);
            Err(e)
        }
        Err(_) => {
            println!("❌ Concurrency test timed out - potential deadlock detected");
            Err(anyhow::anyhow!("Test timed out after {:?}", TIMEOUT_DURATION))
        }
    }
}

/// Test concurrent thread operations
#[tokio::test]
async fn test_concurrent_thread_operations() -> Result<()> {
    const NUM_THREADS: usize = 50;
    const OPERATIONS_PER_THREAD: usize = 10;
    
    let test_execution = async {
        let mut handles = Vec::new();
        
        // Spawn multiple tasks that each create and operate on agent threads
        for i in 0..NUM_THREADS {
            let handle = tokio::spawn(async move {
                let mut thread = AgentThread::new();
                
                // Perform multiple operations on the thread
                for j in 0..OPERATIONS_PER_THREAD {
                    thread.add_user_message(format!("Message {} from thread {}", j, i))?;
                    thread.add_assistant_message(format!("Response {} from thread {}", j, i))?;
                    thread.set_metadata(format!("key_{}", j), format!("value_{}_{}", i, j));
                }
                
                // Verify thread state
                assert_eq!(thread.message_count(), OPERATIONS_PER_THREAD * 2);
                assert_eq!(thread.get_all_metadata().len(), OPERATIONS_PER_THREAD);
                
                Ok::<(), anyhow::Error>(())
            });
            handles.push(handle);
        }
        
        // Wait for all thread operations to complete
        for handle in handles {
            handle.await??;
        }
        
        println!("✅ Successfully completed {} concurrent thread operations", 
                NUM_THREADS * OPERATIONS_PER_THREAD * 2);
        
        Ok::<(), anyhow::Error>(())
    };
    
    // Run with timeout
    timeout(Duration::from_secs(10), test_execution).await??;
    Ok(())
}

/// Stress test with rapid agent creation and destruction
#[tokio::test] 
async fn test_agent_lifecycle_stress() -> Result<()> {
    const ITERATIONS: usize = 100;
    
    let test_execution = async {
        for i in 0..ITERATIONS {
            // Create, use, and drop agents rapidly
            let kernel = KernelBuilder::new().build();
            let agent = ChatCompletionAgent::builder()
                .name(format!("StressAgent{}", i))
                .kernel(kernel)
                .build()?;
            
            let mut thread = AgentThread::new();
            let _response = agent.invoke_async(&mut thread, "Quick test").await?;
            
            // Agent and thread will be dropped here
        }
        
        println!("✅ Successfully completed {} rapid agent lifecycle operations", ITERATIONS);
        Ok::<(), anyhow::Error>(())
    };
    
    timeout(Duration::from_secs(15), test_execution).await??;
    Ok(())
}