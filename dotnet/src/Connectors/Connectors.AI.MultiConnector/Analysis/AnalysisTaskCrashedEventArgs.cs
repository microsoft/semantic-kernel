// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

public class AnalysisTaskCrashedEventArgs
{

    public AnalysisTaskCrashedEventArgs(Exception exception)
    {
        this.Exception = exception;
    }

    public Exception Exception { get; }

}
