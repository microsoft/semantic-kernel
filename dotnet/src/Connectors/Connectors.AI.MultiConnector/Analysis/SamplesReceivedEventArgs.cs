// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

/// <summary>
/// This serves the event triggered when the analysis settings instance receives new samples.
/// </summary>
public class SamplesReceivedEventArgs : EventArgs
{
    public SamplesReceivedEventArgs(List<ConnectorTest> newSamples, AnalysisJob analysisJob)
    {
        this.NewSamples = newSamples;
        this.AnalysisJob = analysisJob;
    }

    public List<ConnectorTest> NewSamples { get; set; }

    public AnalysisJob AnalysisJob { get; set; }
}
