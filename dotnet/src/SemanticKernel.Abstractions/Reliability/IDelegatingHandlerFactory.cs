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
    /// <param name="logger">The <see cref="ILogger"/> instance to be used by the created <see cref="DelegatingHandler"/>, or null if no logger is required.</param>
    /// <returns>A new <see cref="DelegatingHandler"/> instance.</returns>
    DelegatingHandler Create(ILogger? logger);
}
