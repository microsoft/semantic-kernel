// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Controller for agent completions.
/// </summary>
[ApiController]
[Route("agent/completions")]
public class AgentCompletionsController : ControllerBase
{
    private readonly ILogger<AgentCompletionsController> _logger;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentCompletionsController"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    public AgentCompletionsController(ILogger<AgentCompletionsController> logger)
    {
        this._logger = logger;
    }

    /// <summary>
    /// Completes the agent request.
    /// </summary>
    /// <param name="request">The request.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    [HttpPost]
    public async Task<IActionResult> CompleteAsync([FromBody] AgentCompletionRequest request, CancellationToken cancellationToken)
    {
        return this.Ok($"echo: {request.Prompt}");
    }
}
