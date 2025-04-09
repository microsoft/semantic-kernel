// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Plugins;

namespace Agents;

public class DeclarativeAgents(ITestOutputHelper output) : BaseAgentsTest(output)
{
    [InlineData(
        "SchedulingAssistant.json",
        "Read the body of my last five emails, if any contain a meeting request for today, check that it's already on my calendar, if not, call out which email it is.")]
    [Theory]
    public async Task LoadsAgentFromDeclarativeAgentManifestAsync(string agentFileName, string input)
    {
        var kernel = this.CreateKernelWithChatCompletion();
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
