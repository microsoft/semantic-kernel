// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Reliability;

public class NullHttpHandlerFactory : IDelegatingHandlerFactory
{
    public DelegatingHandler Create(ILogger? logger)
    {
        return new NullHttpHandler();
    }
}
