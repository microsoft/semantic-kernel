// Copyright (c) Microsoft. All rights reserved.

using Microsoft.ApplicationInsights.Channel;
using Microsoft.ApplicationInsights.DataContracts;
using Microsoft.ApplicationInsights.Extensibility;

namespace SemanticKernel.Service.Services;

public class AppInsightsUserTelemetryInitializerService : ITelemetryInitializer
{
    public AppInsightsUserTelemetryInitializerService(IHttpContextAccessor httpContextAccessor)
    {
        this._contextAccessor = httpContextAccessor;
    }

    public void Initialize(ITelemetry telemetry)
    {
        if (telemetry is not RequestTelemetry requestTelemetry)
        {
            return;
        }

        var userId = AppInsightsTelemetryService.GetUserIdFromHttpContext(this._contextAccessor);

        telemetry.Context.User.Id = userId;
        requestTelemetry.Properties["userId"] = userId;
    }

    private readonly IHttpContextAccessor _contextAccessor;
}
