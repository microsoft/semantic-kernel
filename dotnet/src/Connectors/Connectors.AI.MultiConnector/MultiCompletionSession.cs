// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents the state variables that are built and processed within a blocking or streaming call to the <see cref="MultiTextCompletion"/>.
/// </summary>
internal struct MultiCompletionSession
{
    /// <summary>
    /// The <see cref="PromptMultiConnectorSettings"/> that are obtained by matching the input prompt to the available Prompt Settings in <see cref="MultiTextCompletion"/>.
    /// </summary>
    public PromptMultiConnectorSettings PromptSettings { get; set; }

    /// <summary>
    /// The input prompt that is passed to <see cref="MultiTextCompletion"/>.
    /// </summary>
    public string InputText { get; set; }

    /// <summary>
    /// The input prompt that is passed to the individual LLM by the <see cref="MultiTextCompletion"/> and may be modified by various settings.
    /// </summary>
    public string CallText { get; set; }

    /// <summary>
    /// The <see cref="CompleteRequestSettings"/> that are passed to <see cref="MultiTextCompletion"/>.
    /// </summary>
    public CompleteRequestSettings InputRequestSettings { get; set; }

    /// <summary>
    /// The <see cref="CompleteRequestSettings"/> that are passed to the individual LLM by the <see cref="MultiTextCompletion"/> and may be modified by various settings.
    /// </summary>
    public CompleteRequestSettings CallRequestSettings { get; set; }

    /// <summary>
    /// A flag that indicates whether the input prompt type identified has a prior configuration or not.
    /// </summary>
    public bool IsNewPrompt { get; set; }

    /// <summary>
    /// The <see cref="NamedTextCompletion"/> that was elicited to answer the call to the <see cref="MultiTextCompletion"/>.
    /// </summary>
    public NamedTextCompletion NamedTextCompletion { get; set; }

    /// <summary>
    /// The <see cref="PromptConnectorSettings"/> that correspond to the current Prompt settings and the chosen Text Completion.
    /// </summary>
    public PromptConnectorSettings PromptConnectorSettings { get; set; }

    /// <summary>
    /// The <see cref="Stopwatch"/> that is used to measure the time taken to complete the call to the <see cref="MultiTextCompletion"/>.
    /// </summary>
    public Stopwatch StopWatch { get; set; }

    /// <summary>
    /// Some operations require to pick on the result, some others not. This property is updated with completion result which is only deferred if needed.
    /// </summary>
    public AsyncLazy<string> ResultProducer { get; set; }
}
