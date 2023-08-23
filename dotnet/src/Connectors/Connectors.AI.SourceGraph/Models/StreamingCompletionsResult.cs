namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Models
{
    using System.Runtime.CompilerServices;
    using Orchestration;
    using SemanticKernel.AI.ChatCompletion;
    using SemanticKernel.AI.TextCompletion;


    internal class StreamingCompletionsResult : IChatStreamingResult, ITextStreamingResult
    {
        private CompletionResponse _response;


        public StreamingCompletionsResult(CompletionResponse completionResponse)
        {
            _response = completionResponse;
        }


        /// <inheritdoc />
        public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<ChatMessageBase>(new Message(SpeakerType.Assistant, _response.Completion?.Trim() ?? string.Empty));
        }


        /// <inheritdoc />
        public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await Task.Yield();

            var list = new List<ChatMessageBase>() { new Message(SpeakerType.Assistant, _response.Completion?.Trim() ?? string.Empty) };

            foreach (var message in list)
            {
                yield return message;
            }

        }


        /// <inheritdoc />
        public ModelResult ModelResult => new ModelResult(_response);


        /// <inheritdoc />
        public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
        {
            return Task.FromResult<string>(_response.Completion?.Trim() ?? string.Empty);
        }


        /// <inheritdoc />
        public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            await foreach (ChatMessageBase message in GetStreamingChatMessageAsync(cancellationToken))
            {
                yield return message.Content;
            }
        }
    }
}
