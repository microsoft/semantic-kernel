// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Config;

/// <summary>
/// A http retry handler that does not retry.
/// </summary>
public sealed class NullHttpHandler : DelegatingHandler
{
}
