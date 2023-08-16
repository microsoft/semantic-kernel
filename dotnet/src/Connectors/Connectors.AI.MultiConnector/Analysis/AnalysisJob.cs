// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Represents a job to be executed by the MultiConnector's analysis
/// </summary>
[DebuggerDisplay("{DebuggerDisplay}")]
public class AnalysisJob : TestEvent
{
    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    public override string DebuggerDisplay => $"{base.DebuggerDisplay}, {this.TextCompletions.Count} Completions to test and analyze";

    public MultiTextCompletionSettings Settings { get; }
    public IReadOnlyList<NamedTextCompletion> TextCompletions { get; }

    public ILogger? Logger { get; }

    public bool SkipPeriods { get; set; }

    public CancellationToken CancellationToken { get; }

    public AnalysisJob(MultiTextCompletionSettings settings, IReadOnlyList<NamedTextCompletion> textCompletions, ILogger? logger, CancellationToken cancellationToken)
    {
        this.Settings = settings;
        this.TextCompletions = textCompletions;
        this.Logger = logger;
        this.CancellationToken = cancellationToken;
    }
}
