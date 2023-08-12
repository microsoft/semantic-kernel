// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

/// <summary>
/// Represents a job to be executed by the MultiConnector's analysis
/// </summary>
public class AnalysisJob : TestEvent
{
    public MultiTextCompletionSettings Settings { get; }
    public IReadOnlyList<NamedTextCompletion> TextCompletions { get; }

    public ILogger? Logger { get; }

    public CancellationToken CancellationToken { get; }

    public AnalysisJob(MultiTextCompletionSettings settings, IReadOnlyList<NamedTextCompletion> textCompletions, ILogger? logger, CancellationToken cancellationToken)
    {
        this.Settings = settings;
        this.TextCompletions = textCompletions;
        this.Logger = logger;
        this.CancellationToken = cancellationToken;
    }
}
