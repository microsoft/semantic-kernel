// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Reliability;

/// <summary>
/// Factory for creating <see cref="DelegatingHandler"/> instances.
/// </summary>
/// <example>
/// Here is an example of how to use the IDelegatingHandlerFactory:
/// <code>
/// IDelegatingHandlerFactory factory = new MyDelegatingHandlerFactory();
/// ILogger logger = new LoggerFactory().CreateLogger("MyLogger");
/// DelegatingHandler handler = factory.Create(logger);
/// </code>
/// </example>
public interface IDelegatingHandlerFactory
{
    /// <summary>
    /// Creates a new <see cref="DelegatingHandler"/> instance with the specified logger.
    /// </summary>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>A new <see cref="DelegatingHandler"/> instance.</returns>
    DelegatingHandler Create(ILoggerFactory? loggerFactory);
}
