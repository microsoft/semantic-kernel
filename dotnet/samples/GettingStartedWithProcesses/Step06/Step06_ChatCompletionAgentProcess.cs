// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace Step06;

public class Step06_ChatCompletionAgentProcess(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    protected override bool ForceOpenAI => true;

    [Fact]
    public async Task ProcessWithChatCompletionAgentsAndSeparateThreadsAsync()
    {
        var agentDefinition1 = new AgentDefinition { Id = "asst_6q5jvZmSxGaGwkiqPv1OmrdA", Name = "Agent1", Type = ChatCompletionAgentFactory.ChatCompletionAgentType };
        var agentDefinition2 = new AgentDefinition { Id = "asst_bM0sHsmAmNhEMj2nxKgPCiYr", Name = "Agent2", Type = ChatCompletionAgentFactory.ChatCompletionAgentType };

        var processBuilder = new ProcessBuilder("chat_completion_agents", stateType: typeof(DefaultProcessState));

        var agent1 = processBuilder.AddStepFromAgent(agentDefinition1)
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent1Complete" }] }]);

        var agent2 = processBuilder.AddStepFromAgent(agentDefinition2)
            .OnComplete([new DeclarativeProcessCondition { Type = DeclarativeProcessConditionType.Default, Emits = [new EventEmission() { EventType = "Agent2Complete" }] }]);

        processBuilder.OnInputEvent("start").SendEventTo(new(agent1));

        processBuilder.ListenFor().Message("Agent1Complete", agent1).SendEventTo(new(agent2, (output) => output));
        processBuilder.ListenFor().Message("Agent2Complete", agent2).StopProcess();

        var process = processBuilder.Build();

        var kernel = CreateKernelWithChatCompletion();

        var context = await process.StartAsync(kernel, new() { Id = "start", Data = "Why are frogs green?" });
        var agent1Result = await context.GetStateAsync();

        Assert.NotNull(context);
        Assert.NotNull(agent1Result);
    }
}
