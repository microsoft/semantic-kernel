// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
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
    private readonly HttpClientHandler? _httpClientHandler;
    private readonly HttpClient _client;

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpSkill"/> class.
    /// </summary>
    public HttpSkill()
    {
        this._httpClientHandler = new() { CheckCertificateRevocationList = true };
        this._client = new HttpClient(this._httpClientHandler);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="HttpSkill"/> class.
    /// </summary>
    /// <param name="client">The HTTP client to use.</param>
    public HttpSkill(HttpClient client)
    {
        this._httpClientHandler = null;
        this._client = client;
    }

    /// <summary>
    /// Sends an HTTP GET request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a GET request to a uri")]
    public async Task<string> GetAsync(string uri)
    {
        var response = await this._client.GetAsync(uri);
        var content = response.Content;
        return await content.ReadAsStringAsync();
    }

    /// <summary>
    /// Sends an HTTP POST request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="context">Contains the body of the request</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a POST request to a uri")]
    [SKFunctionContextParameter(Name = "body", Description = "The body of the request")]
    public async Task<string> PostAsync(string uri, SKContext context)
    {
        using var httpContent = new StringContent(context["body"]);
        var response = await this._client.PostAsync(uri, httpContent);
        var content = response.Content;
        return await content.ReadAsStringAsync();
    }

    /// <summary>
    /// Sends an HTTP PUT request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <param name="context">Contains the body of the request</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a PUT request to a uri")]
    [SKFunctionContextParameter(Name = "body", Description = "The body of the request")]
    public async Task<string> PutAsync(string uri, SKContext context)
    {
        using var httpContent = new StringContent(context["body"]);
        var response = await this._client.PutAsync(uri, httpContent);
        var content = response.Content;
        return await content.ReadAsStringAsync();
    }

    /// <summary>
    /// Sends an HTTP DELETE request to the specified URI and returns the response body as a string.
    /// </summary>
    /// <param name="uri">URI of the request</param>
    /// <returns>The response body as a string.</returns>
    [SKFunction("Makes a DELETE request to a uri")]
    public async Task<string> DeleteAsync(string uri)
    {
        var response = await this._client.DeleteAsync(uri);
        var content = response.Content;
        return await content.ReadAsStringAsync();
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
            this._httpClientHandler?.Dispose();
            this._client.Dispose();
        }
    }
}
