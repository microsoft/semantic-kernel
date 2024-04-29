// Copyright (c) Microsoft. All rights reserved.

using ContentSafety.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;

namespace ContentSafety.Controllers;

/// <summary>
/// Sample chat controller.
/// </summary>
[ApiController]
[Route("[controller]")]
public class ChatController(Kernel kernel) : ControllerBase
{
    private readonly Kernel _kernel = kernel;

    [HttpPost]
    public async Task<IActionResult> PostAsync(ChatModel chat)
    {
        this._kernel.Data["documents"] = chat.Documents;

        return this.Ok((await this._kernel.InvokePromptAsync(chat.Message)).ToString());
    }
}
