// Copyright (c) Microsoft. All rights reserved.
using System.Text;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.Chat;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Plugins;
using Resources;
using static Agents.ChatCompletion_FunctionTermination;

namespace Agents;

public class DeclarativeAgents(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [InlineData("SchedulingAssistant.json", "Read the body of my last five emails, if any contain a meeting request for today, check that it's already on my calendar, if not, call out which email it is.")]
    [Theory]
    public async Task LoadsAgentFromDeclarativeAgentManifestAsync(string agentFileName, string input)
    {
        var kernel = CreateKernelWithFilter();
        var manifestLookupDirectory = Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "..", "Resources", "DeclarativeAgents");
        var manifestFilePath = Path.Combine(manifestLookupDirectory, agentFileName);

        var parameters = await CopilotAgentBasedPlugins.GetAuthenticationParametersAsync();

        var agent = await kernel.CreateChatCompletionAgentFromDeclarativeAgentManifestAsync<ChatCompletionAgent>(manifestFilePath, parameters);

        Assert.NotNull(agent);
        Assert.NotNull(agent.Name);
        Assert.NotEmpty(agent.Name);
        Assert.NotNull(agent.Description);
        Assert.NotEmpty(agent.Description);
        Assert.NotNull(agent.Instructions);
        Assert.NotEmpty(agent.Instructions);

        ChatMessageContent message = new(AuthorRole.User, input);
        ChatHistory chatHistory = [message];
        StringBuilder sb = new();
        await foreach (ChatMessageContent response in agent.InvokeAsync(chatHistory))
        {
            chatHistory.Add(response);
            sb.Append(response.Content);
        }
    }
    private Kernel CreateKernelWithFilter()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        base.AddChatCompletionToKernel(builder);

        // builder.Services.AddSingleton<IAutoFunctionInvocationFilter>(new AutoInvocationFilter());

        return builder.Build();
    }
}
