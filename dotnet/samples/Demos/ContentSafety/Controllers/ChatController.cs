// Copyright (c) Microsoft. All rights reserved.

using ContentSafety.Models;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;

namespace ContentSafety.Controllers;

[ApiController]
[Route("[controller]")]
public class ChatController(Kernel kernel) : ControllerBase
{
    private readonly Kernel _kernel = kernel;

    [HttpPost]
    public async Task<IActionResult> PostAsync(ChatModel chat)
        => this.Ok((await this._kernel.InvokePromptAsync(chat.Message)).ToString());
}
