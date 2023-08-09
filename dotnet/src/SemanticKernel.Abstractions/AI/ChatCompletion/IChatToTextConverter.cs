// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;
public interface IChatToTextConverter
{
    string ChatToText(ChatHistory chat);
    IAsyncEnumerable<IChatStreamingResult> TextResultToChatResult(IAsyncEnumerable<ITextStreamingResult> result);
    IReadOnlyList<IChatResult> TextResultToChatResult(IReadOnlyList<ITextResult> result);

    CompleteRequestSettings ChatSettingsToCompleteSettings(ChatRequestSettings? textSettings);
}
