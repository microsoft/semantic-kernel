// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides configuration and services for workflow execution, including logging and output channels.
/// </summary>
public sealed class HostContext
{
    /// <summary>
    /// Gets the maximum allowed length for expressions evaluated in the workflow.
    /// </summary>
    public int MaximumExpressionLength { get; init; } = 3000;

    /// <summary>
    /// Gets the <see cref="TextWriter"/> used for activity output and diagnostics.
    /// </summary>
    public TextWriter ActivityChannel { get; init; } = Console.Out;

    /// <summary>
    /// Gets the <see cref="ILoggerFactory"/> used to create loggers for workflow components.
    /// </summary>
    public ILoggerFactory LoggerFactory { get; init; } = NullLoggerFactory.Instance;
}
