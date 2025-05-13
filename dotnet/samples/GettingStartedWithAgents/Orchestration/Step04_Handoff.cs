// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace GettingStarted.Orchestration;

/// <summary>
/// Demonstrates how to use the <see cref="HandoffOrchestration"/>.
/// </summary>
public class Step04_Handoff(ITestOutputHelper output) : BaseOrchestrationTest(output)
{
    [Fact]
    public async Task TriageAsync()
    {
        // Initialize plugin
        GithubPlugin githubPlugin = new();
        KernelPlugin plugin = KernelPluginFactory.CreateFromObject(githubPlugin);

        // Define the agents
        ChatCompletionAgent triageAgent =
            this.CreateAgent(
                instructions: "Given a GitHub issue, triage it.",
                name: "TriageAgent",
                description: "An agent that triages GitHub issues");
        ChatCompletionAgent pythonAgent =
            this.CreateAgent(
                instructions: "You are an agent that handles Python related GitHub issues.",
                name: "PythonAgent",
                description: "An agent that handles Python related issues");
        pythonAgent.Kernel.Plugins.Add(plugin);
        ChatCompletionAgent dotnetAgent =
            this.CreateAgent(
                instructions: "You are an agent that handles .NET related GitHub issues.",
                name: "DotNetAgent",
                description: "An agent that handles .NET related issues");
        dotnetAgent.Kernel.Plugins.Add(plugin);

        // Define the orchestration
        OrchestrationMonitor monitor = new();
        HandoffOrchestration orchestration =
            new(OrchestrationHandoffs.Add(triageAgent, dotnetAgent, pythonAgent),
                triageAgent,
                pythonAgent,
                dotnetAgent)
            {
                ResponseCallback = monitor.ResponseCallback,
                LoggerFactory = this.LoggerFactory
            };

        const string InputJson =
            """
            {
              "id": "12345",
              "title": "Bug: SQLite Error 1: 'ambiguous column name:' when including VectorStoreRecordKey in VectorSearchOptions.Filter",
              "body": "Describe the bug\nWhen using column names marked as [VectorStoreRecordData(IsFilterable = true)] in VectorSearchOptions.Filter, the query runs correctly.\nHowever, using the column name marked as [VectorStoreRecordKey] in VectorSearchOptions.Filter, the query throws exception 'SQLite Error 1: ambiguous column name: StartUTC'.\n\nTo Reproduce\nAdd a filter for the column marked [VectorStoreRecordKey]. Since that same column exists in both the vec_TestTable and TestTable, the data for both columns cannot be returned.\n\nExpected behavior\nThe query should explicitly list the vec_TestTable column names to retrieve and should omit the [VectorStoreRecordKey] column since it will be included in the primary TestTable columns.\n\nPlatform\nMicrosoft.SemanticKernel.Connectors.Sqlite v1.46.0-preview\n\nAdditional context\nNormal DBContext logging shows only normal context queries. Queries run by VectorizedSearchAsync() don't appear in those logs and I could not find a way to enable logging in semantic search so that I could actually see the exact query that is failing. It would have been very useful to see the failing semantic query.",
              "labels": []
            }
            """;

        // Start the runtime
        InProcessRuntime runtime = new();
        await runtime.StartAsync();

        // Run the orchestration
        Console.WriteLine($"\n# INPUT:\n{InputJson}\n");
        OrchestrationResult<string> result = await orchestration.InvokeAsync(InputJson, runtime);
        string text = await result.GetValueAsync(TimeSpan.FromSeconds(ResultTimeoutInSeconds));
        Console.WriteLine($"\n# RESULT: {text}");
        Console.WriteLine($"\n# LABELS: {string.Join(",", githubPlugin.Labels["12345"])}\n");

        await runtime.RunUntilIdleAsync();

        Console.WriteLine("\n\nORCHESTRATION HISTORY");
        foreach (ChatMessageContent message in monitor.History)
        {
            this.WriteAgentChatMessage(message);
        }
    }

    private sealed class GithubPlugin
    {
        public Dictionary<string, string[]> Labels { get; } = [];

        [KernelFunction]
        public void AddLabels(string issueId, params string[] labels)
        {
            this.Labels[issueId] = labels;
        }
    }
}
