// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Factory for creating <see cref="DelegatingHandler"/> instances.
/// </summary>
public interface IDelegatingHandlerFactory
{
    DelegatingHandler Create(ILoggerFactory? loggerFactory);
}
