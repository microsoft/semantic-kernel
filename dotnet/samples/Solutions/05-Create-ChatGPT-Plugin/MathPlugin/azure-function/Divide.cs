using System.Globalization;
using System.Net;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Azure.WebJobs.Extensions.OpenApi.Core.Attributes;
using Microsoft.Extensions.Logging;
using Microsoft.OpenApi.Models;

namespace MathPlugin
{
    public class Divide
    {
        private readonly ILogger _logger;

        public Divide(ILoggerFactory loggerFactory)
        {
            _logger = loggerFactory.CreateLogger<Divide>();
        }

        [OpenApiOperation(operationId: "Divide", tags: new[] { "ExecuteFunction" }, Description = "Divide two numbers")]
        [OpenApiParameter(name: "number1", Description = "The first number to divide from", Required = true, In = ParameterLocation.Query)]
        [OpenApiParameter(name: "number2", Description = "The second number to divide by", Required = true, In = ParameterLocation.Query)]
        [OpenApiResponseWithBody(statusCode: HttpStatusCode.OK, contentType: "text/plain", bodyType: typeof(string), Description = "Returns the quotient of the division.")]
        [OpenApiResponseWithBody(statusCode: HttpStatusCode.BadRequest, contentType: "application/json", bodyType: typeof(string), Description = "Returns the error of the input.")]
        [Function("Divide")]
        public HttpResponseData Run([HttpTrigger(AuthorizationLevel.Anonymous, "get", "post")] HttpRequestData req)
        {
            if (req is null)
            {
                throw new System.ArgumentNullException(nameof(req));
            }

            bool result1 = double.TryParse(req.Query["number1"], out double dividend);
            bool result2 = double.TryParse(req.Query["number2"], out double divisor);

            if (result1 && result2 && divisor != 0)
            {
                HttpResponseData response = req.CreateResponse(HttpStatusCode.OK);
                response.Headers.Add("Content-Type", "text/plain");
                double quotient = dividend / divisor;
                response.WriteString(quotient.ToString(CultureInfo.CurrentCulture));

                _logger.LogInformation($"Divide function executed successfully. Dividend: {dividend}, Divisor: {divisor}, Quotient: {quotient}");

                return response;
            }
            else
            {
                HttpResponseData response = req.CreateResponse(HttpStatusCode.BadRequest);
                response.Headers.Add("Content-Type", "application/json");
                response.WriteString("Please pass valid dividend and divisor (non-zero) numbers on the query string or in the request body");

                return response;
            }
        }
    }
}
