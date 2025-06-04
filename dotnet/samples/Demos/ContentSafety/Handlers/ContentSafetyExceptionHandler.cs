// Copyright (c) Microsoft. All rights reserved.

using ContentSafety.Exceptions;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace ContentSafety.Handlers;

/// <summary>
/// Exception handler for content safety scenarios.
/// It allows to return formatted content back to the client with exception details.
/// </summary>
public class ContentSafetyExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext httpContext, Exception exception, CancellationToken cancellationToken)
    {
        if (exception is not TextModerationException and not AttackDetectionException)
        {
            return false;
        }

        var problemDetails = new ProblemDetails
        {
            Status = StatusCodes.Status400BadRequest,
            Title = "Bad Request",
            Detail = exception.Message,
            Extensions = (IDictionary<string, object?>)exception.Data
        };

        httpContext.Response.StatusCode = StatusCodes.Status400BadRequest;

        await httpContext.Response.WriteAsJsonAsync(problemDetails, cancellationToken);

        return true;
    }
}
