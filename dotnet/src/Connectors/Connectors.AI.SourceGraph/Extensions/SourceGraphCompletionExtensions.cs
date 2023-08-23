// // Copyright (c) Microsoft. All rights reserved.
// namespace Microsoft.SemanticKernel.Connectors.AI.SourceGraph.Extensions;
//
// using System.Runtime.CompilerServices;
// using Client;
// using SemanticKernel.AI.ChatCompletion;
//
//
// public static class SourceGraphCompletionExtensions
// {
//
//     // public static async IAsyncEnumerable<string> GenerateMessageStreamAsync(
//     //     this IChatCompletion chatCompletion,
//     //     ChatHistory chat,
//     //     ChatRequestSettings? requestSettings = null,
//     //     [EnumeratorCancellation] CancellationToken cancellationToken = default)
//     // {
//     //     await foreach (var chatCompletionResult in chatCompletion.GetStreamingChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false))
//     //     {
//     //         await foreach (var chatMessageStream in chatCompletionResult.GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
//     //         {
//     //             yield return chatMessageStream.Content;
//     //         }
//     //
//     //         yield break;
//     //     }
//     // }
//     
//     // public static async Task<string> GenerateMessageAsync(
//     //     this ISourceGraphCompletionsClient chatCompletion,
//     //     ChatHistory chat,
//     //     ChatRequestSettings? requestSettings = null,
//     //     CancellationToken cancellationToken = default)
//     // {
//     //     IReadOnlyList<IChatResult>? chatResults = await chatCompletion.GetChatCompletionsAsync(chat, requestSettings, cancellationToken).ConfigureAwait(false);
//     //     var firstChatMessage = await chatResults[0].GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
//     //
//     //     return firstChatMessage.Content;
//     // }
// }

