// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Security.Claims;
using Microsoft.ApplicationInsights;
using Microsoft.AspNetCore.Http;
using SemanticKernel.Service.Diagnostics;

namespace SemanticKernel.Service.Services;

/// <summary>
/// Implementation of the telemetry service interface for Azure Application Insights (AppInsights).
/// </summary>
public class AppInsightsTelemetryService : ITelemetryService
{
    private const string UnknownUserId = "unauthenticated";

    private readonly TelemetryClient _telemetryClient;
    private readonly IHttpContextAccessor _httpContextAccessor;

    /// <summary>
    /// Creates an instance of the app insights telemetry service.
    /// This should be injected into the service collection during startup.
    /// </summary>
    /// <param name="telemetryClient">An AppInsights telemetry client</param>
    /// <param name="httpContextAccessor">Accessor for the current request's http context</param>
    public AppInsightsTelemetryService(TelemetryClient telemetryClient, IHttpContextAccessor httpContextAccessor)
    {
        this._telemetryClient = telemetryClient;
        this._httpContextAccessor = httpContextAccessor;
    }

    /// <inheritdoc/>
    public void TrackSkillFunction(string skillName, string functionName, bool success)
    {
        var properties = new Dictionary<string, string>(this.BuildDefaultProperties())
        {
            { "skillName", skillName },
            { "functionName", functionName },
            { "success", success.ToString() },
        };

        this._telemetryClient.TrackEvent("SkillFunction", properties);
    }

    /// <summary>
    /// Gets the current user's ID from the http context for the current request.
    /// </summary>
    /// <param name="contextAccessor">The http context accessor</param>
    /// <returns></returns>
    public static string GetUserIdFromHttpContext(IHttpContextAccessor contextAccessor)
    {
        var context = contextAccessor.HttpContext;
        if (context == null)
        {
            return UnknownUserId;
        }

        var user = context.User;
        if (user?.Identity?.IsAuthenticated != true)
        {
            return UnknownUserId;
        }

        var userId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (userId == null)
        {
            return UnknownUserId;
        }

        return userId;
    }

    /// <summary>
    /// Prepares a list of common properties that all telemetry events should contain.
    /// </summary>
    /// <returns>Collection of common properties for all telemetry events</returns>
    private Dictionary<string, string> BuildDefaultProperties()
    {
        string? userId = GetUserIdFromHttpContext(this._httpContextAccessor);

        return new Dictionary<string, string>
        {
            { "userId", GetUserIdFromHttpContext(this._httpContextAccessor) }
        };
    }
}
