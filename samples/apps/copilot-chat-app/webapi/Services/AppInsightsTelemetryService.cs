// Copyright (c) Microsoft. All rights reserved.

using System.Security.Claims;
using Microsoft.ApplicationInsights;
using Microsoft.ApplicationInsights.Channel;
using Microsoft.SemanticKernel.Diagnostics;

namespace SemanticKernel.Service.Services;

public class AppInsightsTelemetryService : ITelemetryService
{
    private readonly TelemetryClient _telemetryClient;
    private readonly IHttpContextAccessor _httpContextAccessor;

    public AppInsightsTelemetryService(TelemetryClient telemetryClient, IHttpContextAccessor httpContextAccessor)
    {
        this._telemetryClient = telemetryClient;
        this._httpContextAccessor = httpContextAccessor;
    }

    public void TrackSkillEvent(string skillName, string functionName, bool success)
    {
        var properties = new Dictionary<string, string>(this.BuildDefaultProperties())
        {
            { "skillName", skillName },
            { "functionName", functionName },
            { "success", success.ToString() },
        };

        this._telemetryClient.TrackEvent("CompletionEvent", properties);
    }

    public static string? GetUserIdFromHttpContext(IHttpContextAccessor contextAccessor)
    {
        var context = contextAccessor.HttpContext;
        if (context == null)
        {
            return GetUnknownUserId();
        }

        var user = context.User;
        if (user == null || user.Identity == null || !user.Identity.IsAuthenticated)
        {
            return GetUnknownUserId();
        }

        var userId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;

        if (userId == null)
        {
            return GetUnknownUserId();
        }

        return userId;
    }

    public static string GetUnknownUserId()
    {

        return $"unauthenticated_{Guid.NewGuid()}";
    }

    private Dictionary<string, string> BuildDefaultProperties()
    {
        string? userId = GetUserIdFromHttpContext(this._httpContextAccessor);
        DateTime currentTime = DateTime.UtcNow;

        return new Dictionary<string, string>
        {
            { "userId", userId ?? "unknown" },
            { "timestamp", currentTime.ToString("O") }
        };
    }
}
