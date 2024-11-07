﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

namespace SemanticKernel.Process.IntegrationTests;

/// <summary>
/// Represents the body of a POST request to start a process in the test host.
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
