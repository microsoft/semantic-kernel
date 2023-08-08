// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Net;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;

namespace MathPlugin;

public class Add
{
    private readonly ILogger _logger;

    public Add(ILoggerFactory loggerFactory)
    {
        this._logger = loggerFactory.CreateLogger<Add>();
    }

    [OpenApiOperation(operationId: "Add", tags: new[] { "ExecuteFunction" }, Description = "Add two numbers")]
    [OpenApiParameter(name: "number1", Description = "The first number to add", Required = true, In = ParameterLocation.Query)]
    [OpenApiParameter(name: "number2", Description = "The second number to add", Required = true, In = ParameterLocation.Query)]
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: "text/plain", bodyType: typeof(string), Description = "Returns the sum of the two numbers.")]
    [OpenApiResponseWithBody(statusCode: HttpStatusCode.BadRequest, contentType: "application/json", bodyType: typeof(string), Description = "Returns the error of the input.")]
    [Function("Add")]
    public HttpResponseData Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post")] HttpRequestData req)
    {
        if (req is null)
        {
            throw new System.ArgumentNullException(nameof(req));
        }

        bool result1 = double.TryParse(req.Query["number1"], out double number1);
        bool result2 = double.TryParse(req.Query["number2"], out double number2);

        if (result1 && result2)
        {
            HttpResponseData response = req.CreateResponse(HttpStatusCode.OK);
            response.Headers.Add("Content-Type", "text/plain");
            double sum = number1 + number2;
            response.WriteString(sum.ToString(CultureInfo.CurrentCulture));

            this._logger.LogInformation($"Add function processed a request. Sum: {sum}");

            return response;
        }
        else
        {
            HttpResponseData response = req.CreateResponse(HttpStatusCode.BadRequest);
            response.Headers.Add("Content-Type", "application/json");
            response.WriteString("Please pass two numbers on the query string or in the request body");

            return response;
        }
    }
}
