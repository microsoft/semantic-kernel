// Copyright (c) Microsoft. All rights reserved.

using Microsoft.ApplicationInsights.Channel;
using Microsoft.ApplicationInsights.DataContracts;
using Microsoft.ApplicationInsights.Extensibility;
using Microsoft.AspNetCore.Http;

namespace SemanticKernel.Service.Services;

/// <summary>
/// A telemetry initializer used by the TelemetryClient to fill in data for requests.
/// This implementation injects the id of the current authenticated user (if there is one).
/// </summary>
public class AppInsightsUserTelemetryInitializerService : ITelemetryInitializer
{
    public AppInsightsUserTelemetryInitializerService(IHttpContextAccessor httpContextAccessor)
    {
        this._contextAccessor = httpContextAccessor;
    }

    /// <inheritdoc/>
    public void Initialize(ITelemetry telemetry)
    {
        if (telemetry is not RequestTelemetry requestTelemetry)
        {
            return;
        }

        var userId = AppInsightsTelemetryService.GetUserIdFromHttpContext(this._contextAccessor);

        telemetry.Context.User.Id = userId;
    }

    private readonly IHttpContextAccessor _contextAccessor;
}
