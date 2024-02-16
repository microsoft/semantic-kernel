// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Http;

/// <summary>Provides HTTP header names for common purposes.</summary>
[ExcludeFromCodeCoverage]
internal static class HttpHeaderNames
{
    /// <summary>HTTP header name to use to include the Semantic Kernel package version in all HTTP requests issued by Semantic Kernel.</summary>
    public static string SemanticKernelVersion => "Semantic-Kernel-Version";
}
