// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.CoreSkills;

/// <summary>
/// A skill that provides HTTP functionality.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("http", new HttpSkill());
/// Examples:
/// SKContext["url"] = "https://www.bing.com"
/// {{http.getAsync $url}}
/// {{http.postAsync $url}}
/// {{http.putAsync $url}}
/// {{http.deleteAsync $url}}
/// </example>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1054:URI-like parameters should not be strings",
    Justification = "Semantic Kernel operates on strings")]
public class HttpSkill : IDisposable
{
    private static readonly HttpClientHandler s_httpClientHandler = new() { CheckCertificateRevocationList = true };
    private readonly HttpClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpSkill"/> class.
    /// </summary>
    public HttpSkill() : this(new HttpClient(s_httpClientHandler, disposeHandler: false))
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpSkill"/> class.
    /// </summary>
    /// <param name="client">The HTTP client to use.</param>
    /// <remarks>
    /// <see cref="HttpSkill"/> assumes ownership of the <see cref="HttpClient"/> instance and will dispose it when the skill is disposed.
    /// </remarks>
    public HttpSkill(HttpClient client) =>
        this._client = client;

    /// <summary>
    /// Sends an HTTP GET request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="context">The context for the operation.</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a GET request to a uri")]
    public Task<string> GetAsync(string uri, SKContext context) =>
        this.SendRequestAsync(uri, HttpMethod.Get, cancellationToken: context.CancellationToken);

    /// <summary>
    /// Sends an HTTP POST request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="context">Contains the body of the request</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a POST request to a uri")]
    [SKFunctionContextParameter(Name = "body", Description = "The body of the request")]
    public Task<string> PostAsync(string uri, SKContext context) =>
        this.SendRequestAsync(uri, HttpMethod.Post, new StringContent(context["body"]), context.CancellationToken);

    /// <summary>
    /// Sends an HTTP PUT request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="context">Contains the body of the request</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a PUT request to a uri")]
    [SKFunctionContextParameter(Name = "body", Description = "The body of the request")]
    public Task<string> PutAsync(string uri, SKContext context) =>
        this.SendRequestAsync(uri, HttpMethod.Put, new StringContent(context["body"]), context.CancellationToken);

    /// <summary>
    /// Sends an HTTP DELETE request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="context">The context for the operation.</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a DELETE request to a uri")]
    public Task<string> DeleteAsync(string uri, SKContext context) =>
        this.SendRequestAsync(uri, HttpMethod.Delete, cancellationToken: context.CancellationToken);

    /// <summary>Sends an HTTP request and returns the response content as a string.</summary>
    /// <param name="uri">The URI of the request.</param>
    /// <param name="method">The HTTP method for the request.</param>
    /// <param name="requestContent">Optional request content.</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    private async Task<string> SendRequestAsync(string uri, HttpMethod method, HttpContent? requestContent = null, CancellationToken cancellationToken = default)
    {
        using var request = new HttpRequestMessage(method, uri) { Content = requestContent };
        using var response = await this._client.SendAsync(request, cancellationToken).ConfigureAwait(false);
        return await response.Content.ReadAsStringAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Disposes resources
    /// </summary>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    /// <summary>
    /// Dispose internal resources
    /// </summary>
    /// <param name="disposing">Whether the method is explicitly called by the public Dispose method</param>
    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._client.Dispose();
        }
    }
}
