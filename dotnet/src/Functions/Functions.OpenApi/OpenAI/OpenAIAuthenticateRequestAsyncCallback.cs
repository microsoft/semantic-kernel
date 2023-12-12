// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Represents a delegate that defines the method signature for asynchronously authenticating an HTTP request.
/// </summary>
/// <param name="request">The <see cref="HttpRequestMessage"/> to authenticate.</param>
/// <param name="pluginName">The name of the plugin to be authenticated.</param>
/// <param name="openAIAuthConfig">The <see cref="OpenAIAuthenticationConfig"/> used to authenticate.</param>
/// <param name="cancellationToken">The cancellation token.</param>
/// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
public delegate Task OpenAIAuthenticateRequestAsyncCallback(HttpRequestMessage request, string pluginName, OpenAIAuthenticationConfig openAIAuthConfig, CancellationToken cancellationToken = default);
