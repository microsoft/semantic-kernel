// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI specialized chat completion options.
/// </summary>
public class OpenAIChatCompletionConfig : BaseServiceConfig
{
    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; internal set; }
}
