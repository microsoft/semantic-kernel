// Copyright (c) Microsoft. All rights reserved.

using Magentic.Agents;
using Magentic.Services;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Magentic;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;

namespace Magentic;

internal static class Program
{
    public static async Task<int> Main()
    {
        ConsoleServices console = new();

        console.DisplayProgress("Initializing...");

        IConfigurationRoot configuration = ConfigurationServices.ReadSettings();
        Kernel kernel = KernelServices.CreateKernel(configuration, useOpenAI: true);
        InProcessRuntime runtime = new();

        console.DisplayProgress("Ready!");

        string? input = console.ReadInput("Task");
        if (string.IsNullOrWhiteSpace(input))
        {
            return 0;
        }

        console.DisplayProgress("Initiating task...");

        await runtime.StartAsync().ConfigureAwait(false);

        Agent agent1 = await CoderAgent.CreateAsync(kernel); // %%% MORE AGENTS
        Agent agent2 = ResearchAgent.Create(kernel);
        Agent agent3 = IllustratorAgent.Create(kernel);
        //Agent agent4 = new UserProxyAgent() // %%% USER PROXY

        MagenticOrchestration orchestration = new(runtime, kernel, agent1, agent2, agent3);
        OrchestrationResult<string> result = await orchestration.InvokeAsync(input);
        string answer = await result.GetValueAsync();

        await runtime.RunUntilIdleAsync().ConfigureAwait(false);

        console.DisplayProgress("Completed task!");
        console.DisplayTotalUsage();

        return 0;
    }
}
