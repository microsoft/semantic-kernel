// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Prompty.Core.Parsers;
using Prompty.Core.Renderers;
using Prompty.Core.Types;

namespace Microsoft.SemanticKernel.PromptTemplates.Prompty;
internal class PromptyKernelFunction : KernelFunction
{
    private readonly global::Prompty.Core.Prompty _prompty;
    public PromptyKernelFunction(
        global::Prompty.Core.Prompty prompty)
        : base(prompty.Name, prompty.Description, [])
    {
        this._prompty = prompty;
    }

    public override KernelFunction Clone(string pluginName)
    {
        return new PromptyKernelFunction(this._prompty);
    }

    protected override async ValueTask<FunctionResult> InvokeCoreAsync(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        // step 1
        // get IChatCompletionService from kernel because prompty only work with Azure OpenAI Chat model for now
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        // step 2
        // render prompty based on arguments
        this._prompty.Inputs = arguments.Where(x => x.Value is not null).ToDictionary(x => x.Key, x => x.Value!);
        var renderTemplates = new RenderPromptLiquidTemplate(this._prompty);
        renderTemplates.RenderTemplate();
        var parser = new PromptyChatParser(this._prompty);
        var prompty = parser.ParseTemplate(this._prompty);

        // step 3
        // construct chat history from rendered prompty's message
        var messages = prompty.Messages;

        // because prompty doesn't support function call, we only needs to consider text message at this time
        // parsing image content also not in consideration for now
        var chatHistory = new ChatHistory();
        foreach (var message in messages)
        {
            var role = message["role"];
            var content = message["content"];
            if (role is string && Enum.TryParse<RoleType>(role, out var roleEnum) && content is string)
            {
                var msg = roleEnum switch
                {
                    RoleType.system => new ChatMessageContent(AuthorRole.System, content),
                    RoleType.user => new ChatMessageContent(AuthorRole.User, content),
                    RoleType.assistant => new ChatMessageContent(AuthorRole.Assistant, content),
                    _ => throw new NotSupportedException($"Role {role} is not supported")
                };

                chatHistory.Add(msg);
            }
            else
            {
                throw new ArgumentException("Invalid role or content");
            }
        }

        // step 4
        // construct chat completion request settings
        // because prompty only work with openai model, we can use OpenAIChatCompletionSettings here
        var modelName = prompty.Model.AzureDeployment;
        var key = prompty.Model.ApiKey;
        var settings = new PromptExecutionSettings()
        {
            ModelId = modelName,
        };

        // step 5
        // call chat completion service to get response
        var response = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, cancellationToken: cancellationToken).ConfigureAwait(false);
        return new FunctionResult(this, response, kernel.Culture, response.Metadata);
    }

    protected override IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        throw new NotImplementedException();
    }
}
