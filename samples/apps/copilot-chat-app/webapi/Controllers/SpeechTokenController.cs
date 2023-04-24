// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using SemanticKernel.Service.Config;
using SemanticKernel.Service.Model;

namespace SemanticKernel.Service.Controllers;

[Authorize]
[ApiController]
public class SpeechTokenController : ControllerBase
{
    private sealed class TokenResult
    {
        public string? Token { get; set; }
        public HttpStatusCode? ResponseCode { get; set; }
    }

    private readonly IConfiguration _configuration;
    private readonly ILogger<SpeechTokenController> _logger;

    public SpeechTokenController(IConfiguration configuration, ILogger<SpeechTokenController> logger)
    {
        this._configuration = configuration;
        this._logger = logger;
    }

    /// <summary>
    /// Use the Azure Speech Config key to return an authorization token and region as a Token Response.
    /// </summary>
    [Route("speechToken")]
    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public async Task<ActionResult<SpeechTokenResponse>> GetAsync()
    {
        AzureSpeechConfig azureSpeech = this._configuration.GetSection("AzureSpeech").Get<AzureSpeechConfig>();

        string fetchTokenUri = "https://" + azureSpeech.Region + ".api.cognitive.microsoft.com/sts/v1.0/issueToken";
        string subscriptionKey = azureSpeech.Key;

        TokenResult tokenResult = await this.FetchTokenAsync(fetchTokenUri, subscriptionKey);
        var isSuccess = tokenResult.ResponseCode != HttpStatusCode.NotFound;
        return new SpeechTokenResponse { Token = tokenResult.Token, Region = azureSpeech.Region, IsSuccess = isSuccess };
    }

    private async Task<TokenResult> FetchTokenAsync(string fetchUri, string subscriptionKey)
    {
        // TODO: get the HttpClient from the DI container
        using (var client = new HttpClient())
        {
            client.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", subscriptionKey);
            UriBuilder uriBuilder = new UriBuilder(fetchUri);

            var result = await client.PostAsync(uriBuilder.Uri, null);
            if (result.IsSuccessStatusCode)
            {
                var response = result.EnsureSuccessStatusCode();
                this._logger.LogDebug("Token Uri: {0}", uriBuilder.Uri.AbsoluteUri);
                string token = await result.Content.ReadAsStringAsync();
                return new TokenResult { Token = token, ResponseCode = response.StatusCode };
            }
            else
            {
                return new TokenResult { Token = "", ResponseCode = HttpStatusCode.NotFound };
            }
        }
    }
}
