// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Event arguments for the EvaluationCompleted event.
/// </summary>
public class EvaluationCompletedEventArgs : EventArgs
{
    public MultiCompletionAnalysis CompletionAnalysis { get; set; }

    public EvaluationCompletedEventArgs(MultiCompletionAnalysis completionAnalysis)
    {
        this.CompletionAnalysis = completionAnalysis;
    }
}
