// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Net;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;

namespace MathPlugin;

public class Sqrt
{
    private readonly ILogger _logger;

    public Sqrt(ILoggerFactory loggerFactory)
    {
        this._logger = loggerFactory.CreateLogger<Sqrt>();
    }

    [OpenApiOperation(operationId: "Sqrt", tags: new[] { "ExecuteFunction" }, Description = "Take the square root of a number")]
    [OpenApiParameter(name: "number", Description = "The number to calculate the square root of", Required = true, In = ParameterLocation.Query)]
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: "text/plain", bodyType: typeof(string), Description = "Returns the square root of the number.")]
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.BadRequest, contentType: "application/json", bodyType: typeof(string), Description = "Returns an error message.")]
    [Function("Sqrt")]
    public HttpResponseData Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post")] HttpRequestData req)
    {
        if (req == null)
        {
            throw new ArgumentNullException(nameof(req));
        }

        bool result = double.TryParse(req.Query["number"], out double number);

        if (result && number >= 0)
        {
            double sqrt = Math.Sqrt(number);
            HttpResponseData response = req.CreateResponse(HttpStatusCode.OK);
            response.Headers.Add("Content-Type", "text/plain");
            response.WriteString(sqrt.ToString(CultureInfo.CurrentCulture));

            this._logger.LogInformation($"Calculated square root of {number} to be {sqrt}");

            return response;
        }
        else
        {
            HttpResponseData response = req.CreateResponse(HttpStatusCode.BadRequest);
            response.Headers.Add("Content-Type", "application/json");
            response.WriteString("Please pass a non-negative number on the query string or in the request body");

            return response;
        }
    }
}
