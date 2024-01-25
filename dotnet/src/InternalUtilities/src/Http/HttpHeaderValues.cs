// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Http;

/// <summary>Provides HTTP header values for common purposes.</summary>
[ExcludeFromCodeCoverage]
internal static class HttpHeaderValues
{
    /// <summary>User agent string to use for all HTTP requests issued by Semantic Kernel.</summary>
    public static string UserAgent => "Semantic-Kernel";
}
