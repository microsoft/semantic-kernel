// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector.Analysis;

public class AnalysisTaskCrashedEventArgs : EventArgs
{
    public AnalysisTaskCrashedEventArgs(CrashEvent crashEvent)
    {
        this.CrashEvent = crashEvent;
    }

    public CrashEvent CrashEvent { get; }
}

public class CrashEvent : TestEvent
{
    public CrashEvent(Exception exception)
    {
        this.Exception = exception;
    }

    public Exception Exception { get; }
}
