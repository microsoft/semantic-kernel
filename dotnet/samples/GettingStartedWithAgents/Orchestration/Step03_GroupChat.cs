//// Copyright (c) Microsoft. All rights reserved.

//using Microsoft.AgentRuntime.InProcess;
//using Microsoft.SemanticKernel;
//using Microsoft.SemanticKernel.Agents;
//using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
//using Microsoft.SemanticKernel.ChatCompletion;
//using static Microsoft.SemanticKernel.Agents.Orchestration.GroupChat.ChatMessages;

//namespace GettingStarted.Orchestration;

///// <summary>
///// Demonstrates how to use the <see cref="GroupChatOrchestration"/>.
///// </summary>
//public class Step03_GroupChat(ITestOutputHelper output) : BaseAgentsTest(output)
//{
//    [Fact]
//    public async Task UseGroupChatPatternAsync()
//    {
//        // Define the agents
//        ChatCompletionAgent agent1 =
//                new()
//                {
//                    Instructions = "Count the number of words in the most recent user input without repeating the input.  ALWAYS report the count as a number using the format:\nWords: <count>",
//                    //Name = name,
//                    Description = "Agent 1",
//                    Kernel = this.CreateKernelWithChatCompletion(),
//                };
//        ChatCompletionAgent agent2 =
//                new()
//                {
//                    Instructions = "Count the number of vowels in the most recent user input without repeating the input.  ALWAYS report the count as a number using the format:\nVowels: <count>",
//                    //Name = name,
//                    Description = "Agent 2",
//                    Kernel = this.CreateKernelWithChatCompletion(),
//                };
//        ChatCompletionAgent agent3 =
//                new()
//                {
//                    Instructions = "Count the number of consonants in the most recent user input without repeating the input.  ALWAYS report the count as a number using the format:\nConsonants: <count>",
//                    //Name = name,
//                    Description = "Agent 3",
//                    Kernel = this.CreateKernelWithChatCompletion(),
//                };

//        // Define the pattern
//        InProcessRuntime runtime = new();
//        GroupChatOrchestration orchestration = new(runtime, agent1, agent2, agent3);

//        // Start the runtime
//        await runtime.StartAsync();
//        await orchestration.StartAsync(new ChatMessageContent(AuthorRole.User, "The quick brown fox jumps over the lazy dog"));
//        ChatMessageContent result = await orchestration.Future;
//        Console.WriteLine("RESULT:");
//        this.WriteAgentChatMessage(result);

//        await runtime.RunUntilIdleAsync();
//    }
//}
