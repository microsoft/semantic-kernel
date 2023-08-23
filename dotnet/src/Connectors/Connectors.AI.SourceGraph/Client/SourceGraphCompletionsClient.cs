// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Client;

using Extensions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Models;
using SemanticKernel.AI.ChatCompletion;
using SemanticKernel.AI.TextCompletion;
using StrawberryShake;


internal class SourceGraphCompletionsClient : ISourceGraphCompletionsClient
{
    private readonly ISourceGraphClient _sourceGraphClient;
    private readonly ISourceGraphStreamClient _sourceGraphStreamClient;
    private readonly string _modelId;
    private readonly string _accessToken;
    private readonly ILogger _logger;


    public SourceGraphCompletionsClient(
        string modelId,
        string accessToken,
        ISourceGraphClient sourceGraphClient,
        ISourceGraphStreamClient sourceGraphStreamClient,
        ILogger? logger = null)
    {
        _sourceGraphClient = sourceGraphClient;
        _sourceGraphStreamClient = sourceGraphStreamClient;
        _modelId = modelId;
        _accessToken = accessToken;
        _logger = logger ?? NullLogger.Instance;

    }


    /// <inheritdoc />
    public ChatHistory CreateNewChat(string? instructions = null) => null;


    /// <inheritdoc />
    public async Task<IReadOnlyList<IChatResult>> GetChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        var completionInput = new CompletionsInput().Create(chat, requestSettings);
        IOperationResult<ICompletionsQueryResult> operationResult = await _sourceGraphClient.CompletionsQuery.ExecuteAsync(completionInput, cancellationToken).ConfigureAwait(true);

        try
        {
            operationResult.EnsureNoErrors();
        }
        catch (Exception e)
        {
            Console.WriteLine(e);
            throw;
        }

        return new[] { new CompletionResult(operationResult.Data) };
    }


    /// <inheritdoc />
    public async IAsyncEnumerable<IChatStreamingResult> GetStreamingChatCompletionsAsync(ChatHistory chat, ChatRequestSettings? requestSettings = null, CancellationToken cancellationToken = default)
    {
        var completionInput = new CompletionsRequest().Create(chat, requestSettings);
        List<StreamingCompletionsResult> streamingChatChoices = new();
        var completionResponse = await _sourceGraphStreamClient.CompleteAsync(completionInput, response =>
        {
            streamingChatChoices.Add(new StreamingCompletionsResult(response));
        }, cancellationToken).ConfigureAwait(false);

        if (completionResponse != null)
        {
            streamingChatChoices.Add(new StreamingCompletionsResult(completionResponse));
        }

        foreach (StreamingCompletionsResult response in streamingChatChoices)
        {
            yield return response;
        }
    }


    /// <inheritdoc />
    public async Task<IReadOnlyList<ITextResult>> GetCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default)
    {
        return null;
    }


    /// <inheritdoc />
    public IAsyncEnumerable<ITextStreamingResult> GetStreamingCompletionsAsync(string text, CompleteRequestSettings requestSettings, CancellationToken cancellationToken = default) => null;

}
