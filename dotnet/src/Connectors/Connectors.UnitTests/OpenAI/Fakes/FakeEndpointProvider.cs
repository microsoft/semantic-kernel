// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace SemanticKernel.Connectors.UnitTests.OpenAI;

public class FakeEndpointProvider : IEndpointProvider
{
    public Uri ModerationEndpoint { get; } = new Uri("https://example.com/completions/");
}
