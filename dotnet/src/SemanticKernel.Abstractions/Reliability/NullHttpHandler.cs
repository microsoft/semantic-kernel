// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Reliability;

/// <summary>
/// A http retry handler that does not retry.
/// </summary>
public class NullHttpHandler : DelegatingHandler
{
}
