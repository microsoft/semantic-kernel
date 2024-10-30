// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Contains information required to start a process.
/// </summary>
public record ProcessStartRequest
{
    /// <summary>
    /// The process to start.
    /// </summary>
    public required DaprProcessInfo Process { get; set; }

    /// <summary>
    /// The initial event to send to the process.
    /// </summary>
    public required KernelProcessEvent InitialEvent { get; set; }
}
