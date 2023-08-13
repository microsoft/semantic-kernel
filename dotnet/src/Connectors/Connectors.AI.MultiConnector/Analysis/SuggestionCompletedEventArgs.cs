// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// Event arguments for the SuggestionCompleted event.
/// </summary>
public class SuggestionCompletedEventArgs : EventArgs
{
    public MultiCompletionAnalysis CompletionAnalysis { get; set; }

    public MultiTextCompletionSettings SuggestedSettings { get; set; }

    public SuggestionCompletedEventArgs(MultiCompletionAnalysis completionAnalysis, MultiTextCompletionSettings suggestedSettings)
    {
        this.CompletionAnalysis = completionAnalysis;
        this.SuggestedSettings = suggestedSettings;
    }
}
