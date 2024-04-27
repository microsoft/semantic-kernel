// Copyright (c) Microsoft. All rights reserved.

using ContentSafety.Exceptions;
using Microsoft.AspNetCore.Diagnostics;
using Microsoft.AspNetCore.Mvc;

namespace ContentSafety.Handlers;

public class ContentSafetyExceptionHandler : IExceptionHandler
{
    public async ValueTask<bool> TryHandleAsync(HttpContext httpContext, Exception exception, CancellationToken cancellationToken)
    {
        if (exception is not TextModerationException)
        {
            return false;
        }

        var problemDetails = new ProblemDetails
        {
            Status = StatusCodes.Status400BadRequest,
            Title = "Bad Request",
            Detail = exception.Message
        };

        httpContext.Response.StatusCode = StatusCodes.Status400BadRequest;

        await httpContext.Response.WriteAsJsonAsync(problemDetails, cancellationToken);

        return true;
    }
}
