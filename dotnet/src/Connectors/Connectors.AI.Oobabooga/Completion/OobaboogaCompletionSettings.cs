// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;

public class OobaboogaCompletionSettings<TParameters>
    where TParameters : OobaboogaCompletionParameters, new()
{
    /// <summary>
    /// Determines whether or not to use the overlapping SK settings for the completion request. Prompt is still provided by SK.
    /// </summary>
    public bool OverrideSKSettings { get; set; }

    public TParameters OobaboogaParameters { get; set; } = new();
}

public class OobaboogaTextCompletionSettings : OobaboogaCompletionSettings<OobaboogaCompletionParameters>
{
}

public class OobaboogaChatCompletionSettings : OobaboogaCompletionSettings<OobaboogaChatCompletionParameters>
{
}
