// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using SemanticKernel.Service.CopilotChat.Options;
using SemanticKernel.Service.Services;

namespace SemanticKernel.Service.CopilotChat.Controllers;

[ApiController]
[Authorize]
public class ContentModeratorController : ControllerBase
{
    private readonly ILogger<ContentModeratorController> _logger;
    private readonly ContentModeratorOptions _options;
    private readonly AzureContentModerator? _contentModerator = null;

    /// <summary>
    /// The constructor of ContentModeratorController.
    /// </summary>
    /// <param name="logger">The logger.</param>
    /// <param name="ContentModeratorOptions">The content moderation options.</param>
    /// <param name="contentModerator">The content moderation service.</param>
    public ContentModeratorController(
        ILogger<ContentModeratorController> logger,
        IOptions<ContentModeratorOptions> ContentModeratorOptions,
        AzureContentModerator? contentModerator = null)
    {
        this._logger = logger;
        this._contentModerator = contentModerator;
        this._options = ContentModeratorOptions.Value;
    }

    /// <summary>
    /// Detect sensitive image content.
    /// </summary>
    /// <param name="base64Image">The base64 encoded image for analysis.</param>
    /// <returns>The HTTP action result.</returns>
    [HttpPost]
    [Route("contentModerator/image")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status404NotFound)]
    public async Task<ActionResult<Dictionary<string, AnalysisResult>>> ImageAnalysisAsync(
        [FromBody] string base64Image)
    {
        if (!this._options.Enabled)
        {
            return this.NotFound("Content Moderation is currently disabled.");
        }

        return await this._contentModerator!.ImageAnalysisAsync(base64Image, default);
    }

    /// <summary>
    /// Gets the status of content moderation.
    /// </summary>
    /// <returns></returns>
    [HttpGet]
    [Route("contentModerator/status")]
    [ProducesResponseType(StatusCodes.Status200OK)]
    public bool ContentModeratorStatus()
    {
        return this._options.Enabled;
    }
}
