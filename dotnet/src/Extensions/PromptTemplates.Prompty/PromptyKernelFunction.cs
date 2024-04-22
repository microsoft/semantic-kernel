// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Prompty.Core;

namespace Microsoft.SemanticKernel.Experimental.Prompty;
public class PromptyKernelFunction : KernelFunction
{
    private readonly Core.Prompty _prompty;

    internal PromptyKernelFunction(Core.Prompty prompty)
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

        (ChatHistory chatHistory, PromptExecutionSettings settings) = this.CreateChatHistoryAndSettings(arguments);

        // step 5
        // call chat completion service to get response
        var response = await chatCompletionService.GetChatMessageContentAsync(chatHistory, settings, cancellationToken: cancellationToken).ConfigureAwait(false);
        return new FunctionResult(this, response, kernel.Culture, response.Metadata);
    }

    protected override async IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(Kernel kernel, KernelArguments arguments, CancellationToken cancellationToken)
    {
        // step 1
        // get IChatCompletionService from kernel because prompty only work with Azure OpenAI Chat model for now
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        (ChatHistory chatHistory, PromptExecutionSettings settings) = this.CreateChatHistoryAndSettings(arguments);


        // step 5
        // call chat completion service to get response
        var asyncReference = chatCompletionService.GetStreamingChatMessageContentsAsync(chatHistory, settings, cancellationToken: cancellationToken).ConfigureAwait(false);
        await foreach (var content in asyncReference.ConfigureAwait(false))
        {
            cancellationToken.ThrowIfCancellationRequested();

            yield return typeof(TResult) switch
            {
                _ when typeof(TResult) == typeof(string)
                    => (TResult)(object)content.ToString(),

                _ when content is TResult contentAsT
                    => contentAsT,

                _ when content.InnerContent is TResult innerContentAsT
                    => innerContentAsT,

                _ when typeof(TResult) == typeof(byte[])
                    => (TResult)(object)content.ToByteArray(),

                _ => throw new NotSupportedException($"The specific type {typeof(TResult)} is not supported. Support types are {typeof(StreamingTextContent)}, string, byte[], or a matching type for {typeof(StreamingTextContent)}.{nameof(StreamingTextContent.InnerContent)} property")
            };
        }
    }

    private (ChatHistory, PromptExecutionSettings) CreateChatHistoryAndSettings(KernelArguments arguments)
    {
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

        return (chatHistory, settings);
    }
}
