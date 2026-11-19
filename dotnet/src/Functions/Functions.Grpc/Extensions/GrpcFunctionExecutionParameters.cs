// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Plugins.Grpc;

/// <summary>
/// gRPC function execution parameters.
/// </summary>
[Experimental("SKEXP0040")]
public class GrpcFunctionExecutionParameters
{
    /// <summary>
    /// HttpClient to use for sending gRPC requests.
    /// </summary>
    public HttpClient? HttpClient { get; set; }

    /// <summary>
    /// Developer-provided address override for the gRPC channel.
    /// When set, this address is used instead of the one from the .proto document.
    /// This value is controlled by the developer, not by the LLM.
    /// </summary>
    public Uri? AddressOverride { get; set; }

    /// <summary>
    /// Gets or sets the allowed gRPC server base addresses.
    /// If set, only requests to addresses that start with one of these base URIs will be permitted.
    /// This helps prevent Server-Side Request Forgery (SSRF) attacks.
    /// If null, no base address restriction is applied (scheme validation still applies).
    /// </summary>
    public IReadOnlyList<Uri>? AllowedAddresses { get; set; }

    /// <summary>
    /// Gets or sets the allowed URI schemes for gRPC server addresses.
    /// If null or empty, only <c>https</c> is permitted.
    /// </summary>
    public IReadOnlyList<string>? AllowedSchemes { get; set; }
}
