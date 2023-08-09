// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

public class OptimizationCompletedEventArgs : EventArgs
{
    public MultiCompletionAnalysis Analysis { get; set; }
    public MultiTextCompletionSettings SuggestedSettings { get; set; }

    public OptimizationCompletedEventArgs(MultiCompletionAnalysis analysis, MultiTextCompletionSettings suggestedSettings)
    {
        this.Analysis = analysis;
        this.SuggestedSettings = suggestedSettings;
    }
}
