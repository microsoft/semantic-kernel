// Copyright (c) Microsoft. All rights reserved.

// TODO: replace this controller with a better health check:
// https://learn.microsoft.com/en-us/aspnet/core/host-and-deploy/health-checks?view=aspnetcore-7.0

using Microsoft.AspNetCore.Mvc;

namespace SemanticKernel.Service.Skills;

[Route("[controller]")]
[ApiController]
public class HealthProbeController : ControllerBase
{
    [HttpGet]
    public ActionResult<string> VerifyLiveness()
    {
        return "Semantic Kernel service is live.";
    }
}
