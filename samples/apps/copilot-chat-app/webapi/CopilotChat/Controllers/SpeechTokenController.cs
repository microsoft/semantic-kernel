// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using SemanticKernel.Service.CopilotChat.Models;
using SemanticKernel.Service.CopilotChat.Options;

namespace SemanticKernel.Service.CopilotChat.Controllers;

[Authorize]
[ApiController]
public class SpeechTokenController : ControllerBase
{
    private sealed class TokenResult
    {
        public string? Token { get; set; }
        public HttpStatusCode? ResponseCode { get; set; }
    }

    private readonly ILogger<SpeechTokenController> _logger;
    private readonly AzureSpeechOptions _options;

    public SpeechTokenController(IOptions<AzureSpeechOptions> options, ILogger<SpeechTokenController> logger)
    {
        this._logger = logger;
        this._options = options.Value;
    }

    /// <summary>
    /// Get an authorization token and region
    /// </summary>
    [Route("speechToken")]
    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public async Task<ActionResult<SpeechTokenResponse>> GetAsync()
    {
        // Azure Speech token support is optional. If the configuration is missing or incomplete, return an unsuccessful token response.
        if (string.IsNullOrWhiteSpace(this._options.Region) ||
            string.IsNullOrWhiteSpace(this._options.Key))
        {
            return new SpeechTokenResponse { IsSuccess = false };
        }

        string fetchTokenUri = "https://" + this._options.Region + ".api.cognitive.microsoft.com/sts/v1.0/issueToken";

        TokenResult tokenResult = await this.FetchTokenAsync(fetchTokenUri, this._options.Key);
        var isSuccess = tokenResult.ResponseCode != HttpStatusCode.NotFound;
        return new SpeechTokenResponse { Token = tokenResult.Token, Region = this._options.Region, IsSuccess = isSuccess };
    }

    private async Task<TokenResult> FetchTokenAsync(string fetchUri, string subscriptionKey)
    {
        // TODO: get the HttpClient from the DI container
        using var client = new HttpClient();
        client.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", subscriptionKey);
        UriBuilder uriBuilder = new(fetchUri);

        var result = await client.PostAsync(uriBuilder.Uri, null);
        if (result.IsSuccessStatusCode)
        {
            var response = result.EnsureSuccessStatusCode();
            this._logger.LogDebug("Token Uri: {0}", uriBuilder.Uri.AbsoluteUri);
            string token = await result.Content.ReadAsStringAsync();
            return new TokenResult { Token = token, ResponseCode = response.StatusCode };
        }

        return new TokenResult { Token = "", ResponseCode = HttpStatusCode.NotFound };
    }
}
