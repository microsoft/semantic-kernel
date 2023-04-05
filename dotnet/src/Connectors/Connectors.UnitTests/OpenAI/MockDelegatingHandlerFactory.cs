// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Reliability;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

/// <summary>
/// MockDelegatingHandlerFactory for OpenAI test purposes.
/// </summary>
internal class MockDelegatingHandlerFactory : IDelegatingHandlerFactory
{
    private DelegatingHandler _delegatingHandler;

    public MockDelegatingHandlerFactory(DelegatingHandler delegatingHandler)
    {
        this._delegatingHandler = delegatingHandler;
    }

    public DelegatingHandler Create(ILogger log)
    {
        return this._delegatingHandler;
    }
}
