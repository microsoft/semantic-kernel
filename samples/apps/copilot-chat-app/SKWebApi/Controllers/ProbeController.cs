// Copyright (c) Microsoft. All rights reserved.

// TODO: replace this controller with a better health check:
// https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-7.0

using Microsoft.AspNetCore.Mvc;

namespace SemanticKernel.Service.Controllers;

[Route("[controller]")]
[ApiController]
public class ProbeController : ControllerBase
{
    [HttpGet]
    public ActionResult<string> Get()
    {
        return "Semantic Kernel service up and running";
    }
}
