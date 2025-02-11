// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Process.Internal;
internal class ProcessEventData
{
    /// <summary>
    /// SK Process Event Id, id assigned during runtime
    /// </summary>
    public string EventId { get; init; } = string.Empty;

    /// <summary>
    /// SK Process Event Name, human readable, defined when creating the process builder
    /// </summary>
    public string EventName { get; init; } = string.Empty;
}
