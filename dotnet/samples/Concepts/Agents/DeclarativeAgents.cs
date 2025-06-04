// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace Agents;

/// <summary>
/// Sample showing how declarative agents can be defined through JSON manifest files.
/// Demonstrates how to load and configure an agent from a declarative manifest that specifies:
/// - The agent's identity (name, description, instructions)
/// - The agent's available actions/plugins
/// - Authentication parameters for accessing external services
/// </summary>
/// <remarks>
/// The test uses a SchedulingAssistant example that can:
/// - Read emails for meeting requests
/// - Check calendar availability
/// - Process scheduling-related tasks
/// The agent is configured via "SchedulingAssistant.json" manifest which defines the required
/// plugins and capabilities.
/// </remarks>
public class DeclarativeAgents(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task LoadsAgentFromDeclarativeAgentManifest(bool useChatClient)
    {
        var agentFileName = "SchedulingAssistant.json";
        var input = "Read the body of my last five emails, if any contain a meeting request for today, check that it's already on my calendar, if not, call out which email it is.";

        var kernel = this.CreateKernelWithChatCompletion(useChatClient, out var chatClient);
        kernel.AutoFunctionInvocationFilters.Add(new ExpectedSchemaFunctionFilter());
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

        ChatHistoryAgentThread agentThread = new();

        var kernelArguments = new KernelArguments(new PromptExecutionSettings
        {
            FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
                    options: new FunctionChoiceBehaviorOptions
                    {
                        AllowStrictSchemaAdherence = true
                    }
                )
        });

        var responses = await agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, input), agentThread, options: new() { KernelArguments = kernelArguments }).ToArrayAsync();
        Assert.NotEmpty(responses);

        chatClient?.Dispose();
    }

    private sealed class ExpectedSchemaFunctionFilter : IAutoFunctionInvocationFilter
    {
        //TODO: this eventually needs to be added to all CAP or DA but we're still discussing where should those facilitators live
        public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
        {
            await next(context);

            if (context.Result.ValueType == typeof(RestApiOperationResponse))
            {
                var openApiResponse = context.Result.GetValue<RestApiOperationResponse>();
                if (openApiResponse?.ExpectedSchema is not null)
                {
                    openApiResponse.ExpectedSchema = null;
                }
            }
        }
    }
}
