// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;
using AIPlugins.AzureFunctions.Extensions;
using Microsoft.SemanticKernel;
using System.Net.Http;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using System;
using AIPlugins.AzureFunctions.LinkedIn.Models;

namespace AIPlugins.AzureFunctions.LinkedIn;

/// <summary>
/// Represents a host for managing and interacting with LinkedIn skills.
/// </summary>
public class LinkedInSkillHost
{
    /// <summary>
    /// The logger used for logging in the LinkedInSkillHost class.
    /// </summary>
    private readonly ILogger _logger;

    /// <summary>
    /// The kernel used for managing the operations in the LinkedInSkillHost class.
    /// </summary>
    private readonly IKernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="LinkedInSkillHost"/> class.
    /// </summary>
    /// <param name="kernel">The IKernel used for dependency injection.</param>
    /// <param name="loggerFactory">The ILoggerFactory used to create loggers.</param>
    public LinkedInSkillHost(IKernel kernel, ILoggerFactory loggerFactory)
    {
        this._logger = loggerFactory.CreateLogger<LinkedInSkillHost>();
        this._kernel = kernel;
    }

    [Function("ChatGPT")]
    [OpenApiIgnore]
    public Task<HttpResponseData> GetAIPluginSpecAsync([HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = ".well-known/ai-plugin.json")] HttpRequestData req)
    {
        this._logger.LogInformation("HTTP trigger processed a request for function GetAIPluginSpecAsync.");
        return AIPluginHelpers.GenerateAIPluginJsonResponseAsync(req, "LinkedIn", "API for LinkedIn", "This plugin can make a post to LinkedIn which includes text and an image");
    }

    [Function("api/LinkedIn/Post")]
    [OpenApiOperation(operationId: "Share", tags: new[] { "LinkedIn" }, Description = "Share text content with image with your LinkedIn network")]
    [OpenApiRequestBody("application/json", typeof(PostModel), Required = true, Description = "Text and image to share.")]
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: "text/plain", bodyType: typeof(string), Description = "The OK response")]
    public async Task<HttpResponseData> PostContentAsync([Microsoft.Azure.Functions.Worker.HttpTrigger(AuthorizationLevel.Anonymous, "post")] HttpRequestData req)
    {
        this._logger.LogInformation("HTTP trigger processed a request for post content.");

        try
        {
            var (text, imageUrl) = await this.GetPostDetailsAsync(req);

            await this.SharePostAsync(text, imageUrl);
        }
        catch (BadRequestException ex)
        {
            this._logger.LogError("Invalid request - {0}", ex.Message);
            return req.CreateResponse(HttpStatusCode.BadRequest);
        }

        return req.CreateResponse(HttpStatusCode.OK);
    }

    /// <summary>
    /// Asynchronously retrieves the details of a post.
    /// </summary>
    /// <param name="req">The HttpRequestData object representing the request to get post details.</param>
    /// <returns>A Task that represents the asynchronous operation. The task result contains a tuple with two strings. The first string represents the post title and the second string represents the post content.</returns>
    private async Task<(string, string)> GetPostDetailsAsync(HttpRequestData req)
    {
        var contentType = req.Headers.GetValues("Content-Type").SingleOrDefault();
        if (string.IsNullOrEmpty(contentType) || contentType != "application/json")
        {
            this._logger.LogError("Invalid request: Unexpected content type. Only 'application/json' content type is supported.");
            throw new BadRequestException("Invalid request: Unexpected content type. Only 'application/json' content type is supported.");
        }

        var body = await req.ReadFromJsonAsync<PostModel>();
        if (body == null || body.Text == null || body.ImageUrl == null)
        {
            this._logger.LogError("Invalid request: Unsupported payload schema.");
            throw new BadRequestException("Invalid request: Unsupported payload schema.");
        }

        string image = await this.LoadImageAsync(body.ImageUrl);

        return (body.Text, image);
    }

    /// <summary>
    /// Asynchronously loads an image from the provided URL.
    /// </summary>
    /// <param name="imageUrl">The URL of the image to load.</param>
    /// <returns>A Task representing the asynchronous operation, with a string as the result containing the loaded image data.</returns>
    private async Task<string> LoadImageAsync(Uri imageUrl)
    {
        using (HttpClient httpClient = new())
        {
            byte[] imageBytes = await httpClient.GetByteArrayAsync(imageUrl);

            return Convert.ToBase64String(imageBytes);
        }
    }

    /// <summary>
    /// Asynchronously shares a post on LinkedIn.
    /// </summary>
    /// <param name="text">The text content of the post.</param>
    /// <param name="encodedImage">The encoded image to be included in the post.</param>
    /// <returns>A <see cref="Task"/> representing the asynchronous operation.</returns>
    private async Task SharePostAsync(string text, string encodedImage)
    {
        var authToken = Environment.GetEnvironmentVariable("LinkedInAccessToken");

        //get the LinkedIn PersonUPN
        var contextVariables = new ContextVariables();
        contextVariables.Set(LinkedInSkill.Parameters.AuthToken, authToken);

        var personUpnResult = await this._kernel.RunAsync(contextVariables, this._kernel.Skills.GetFunction(nameof(LinkedInSkill), "GetPersonUpn"));

        var personUpn = personUpnResult.Result;

        contextVariables = new ContextVariables();
        contextVariables.Set(LinkedInSkill.Parameters.AuthToken, authToken);
        contextVariables.Set(LinkedInSkill.Parameters.PersonURN, personUpn);
        contextVariables.Set(LinkedInSkill.Parameters.Image, encodedImage);
        var uploadImageResult = await this._kernel.RunAsync(contextVariables, this._kernel.Skills.GetFunction(nameof(LinkedInSkill), "UploadImageV2"));

        //write the LI post which has the reference to the image included
        contextVariables = new ContextVariables(text);
        contextVariables.Set(LinkedInSkill.Parameters.AuthToken, authToken);
        contextVariables.Set(LinkedInSkill.Parameters.PersonURN, personUpn);
        contextVariables.Set(LinkedInSkill.Parameters.ImageAsset, uploadImageResult.Result); //the image asset is optional, if it's not included it will just be text

        var result = await this._kernel.RunAsync(contextVariables, this._kernel.Skills.GetFunction(nameof(LinkedInSkill), "PostContent"));
    }
}
