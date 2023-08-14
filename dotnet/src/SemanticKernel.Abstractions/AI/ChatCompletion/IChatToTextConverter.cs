// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;
public interface IChatToTextConverter
{
    string ChatToText(ChatHistory chat);
    CompleteRequestSettings ChatSettingsToCompleteSettings(ChatRequestSettings? textSettings);
    IReadOnlyList<IChatResult> TextResultToChatResult(IReadOnlyList<ITextResult> result);
    IAsyncEnumerable<IChatStreamingResult> TextStreamingResultToChatStreamingResult(IAsyncEnumerable<ITextStreamingResult> result);

}
