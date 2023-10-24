// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;

/// <summary>
/// Represents a delegate that defines the method signature for asynchronously authenticating an HTTP request.
/// </summary>
/// <param name="request">The <see cref="HttpRequestMessage"/> to authenticate.</param>
/// <param name="authConfig">The <see cref="OpenAIManifestAuthenticationConfig"/> used to authenticate.</param>
/// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
public delegate Task AuthenticateRequestAsyncCallback(HttpRequestMessage request, OpenAIManifestAuthenticationConfig? authConfig = null);
