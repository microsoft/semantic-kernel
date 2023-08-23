namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models;

using Orchestration;
using SemanticKernel.AI.ChatCompletion;
using SemanticKernel.AI.TextCompletion;


internal class CompletionResult : IChatResult, ITextResult
{
    private readonly ICompletionsQueryResult _completionsQueryResult;


    public CompletionResult(ICompletionsQueryResult? completionResponse)
    {
        _completionsQueryResult = completionResponse;
    }


    /// <inheritdoc />
    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult<ChatMessageBase>(new Message(SpeakerType.Assistant, _completionsQueryResult.Completions.Trim()));
    }


    /// <inheritdoc />
    public ModelResult ModelResult => new ModelResult(_completionsQueryResult);


    /// <inheritdoc />
    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult<string>(_completionsQueryResult.Completions.Trim());
    }
}
