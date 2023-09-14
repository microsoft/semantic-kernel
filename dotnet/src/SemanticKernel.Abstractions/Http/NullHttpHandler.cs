// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// A http retry handler that does nothing.
/// </summary>
public sealed class NullHttpHandler : DelegatingHandler
{
}
