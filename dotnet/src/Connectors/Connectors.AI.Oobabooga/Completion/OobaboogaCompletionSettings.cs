// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion;

public class OobaboogaCompletionSettings
{
    /// <summary>
    /// Determines whether or not to use the overlapping SK settings for the completion request. Prompt is still provided by SK.
    /// </summary>
    public bool OverrideSKSettings { get; set; }
}

public class OobaboogaCompletionSettings<TParameters> : OobaboogaCompletionSettings where TParameters : OobaboogaCompletionParameters, new()
{
    public TParameters OobaboogaParameters { get; set; } = new();
}

public class OobaboogaTextCompletionSettings : OobaboogaCompletionSettings<OobaboogaCompletionParameters>
{
}

public class OobaboogaChatCompletionSettings : OobaboogaCompletionSettings<OobaboogaChatCompletionParameters>
{
}
