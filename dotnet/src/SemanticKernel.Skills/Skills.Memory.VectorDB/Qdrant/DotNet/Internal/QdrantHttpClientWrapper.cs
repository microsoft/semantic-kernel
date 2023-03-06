// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json.Linq;
using Qdrant.DotNet.Internal.Diagnostics;

namespace Qdrant.DotNet.Internal;

internal class QdrantHttpClientWrapper
{
    public string BaseAddress
    {
        get { return this._httpClient.BaseAddress.ToString(); }
        set { this._httpClient.BaseAddress = SanitizeEndpoint(value); }
    }

    public int AddressPort
    {
        get { return this._httpClient.BaseAddress.Port; }
        set { this._httpClient.BaseAddress = SanitizeEndpoint(this.BaseAddress, value); }
    }

    public QdrantHttpClientWrapper(HttpClient client, ILogger logger)
    {
        this._httpClient = client;
        this._log = logger;
    }

    public async Task<(HttpResponseMessage response, string responseContent)> ExecuteHttpRequestAsync(HttpRequestMessage request)
    {
        HttpResponseMessage response = await this._httpClient.SendAsync(request);

        string responseContent = await response.Content.ReadAsStringAsync();
        if (response.IsSuccessStatusCode)
        {
            // TODO: Replace with a System.Text.Json implementation
            dynamic tmp = JObject.Parse(responseContent);
            if (tmp != null && this._log.IsEnabled(LogLevel.Debug))
            {
                this._log.LogDebug("Qdrant response time: {0}", (double)tmp.time);
            }

            this._log.LogTrace("Qdrant response: {0}", responseContent);
        }
        else
        {
            this._log.LogWarning("Qdrant response: {0}", responseContent);
        }

        return (response, responseContent);
    }

    #region private ================================================================================

    private readonly HttpClient _httpClient;
    private readonly ILogger _log;

    private static Uri SanitizeEndpoint(string endpoint)
    {
        Verify.IsValidUrl(nameof(endpoint), endpoint, false, true, false);
        return new Uri(endpoint);
    }

    private static Uri SanitizeEndpoint(string endpoint, int port)
    {
        UriBuilder builder = new UriBuilder(SanitizeEndpoint(endpoint))
        { Port = port };
        return builder.Uri;

    }

    #endregion
}
