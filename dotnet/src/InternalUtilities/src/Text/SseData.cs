// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Text;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

/// <summary>
/// Represents a single Server-Sent Events (SSE) data object.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class SseData
{
    /// <summary>
    /// The name of the sse event.
    /// </summary>
    public string? EventName { get; }

    /// <summary>
    /// Represents the type of data parsed from SSE message.
    /// </summary>
    public Type DataType { get; }

    /// <summary>
    /// Represents the data parsed from SSE message.
    /// </summary>
    public object Data { get; }

    /// <summary>
    /// Represents a single Server-Sent Events (SSE) data object.
    /// </summary>
    /// <param name="eventName">The name of the sse event.</param>
    /// <param name="data">The data parsed from SSE message.</param>
    public SseData(string? eventName, object data)
    {
        Verify.NotNull(data);

        this.EventName = eventName;
        this.DataType = data.GetType();
        this.Data = data;
    }
}
