// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Http;
internal static class HttpClientExtensions
{
    /// <summary>
    /// Handles Http response.
    /// </summary>
    /// <typeparam name="T">The response type.</typeparam>
    /// <param name="response">The Http response message.</param>
    /// <returns>The deserialized response.</returns>
    /// <exception cref="AIException">The exception thrown in case response is not successful.</exception>
    internal static async Task<T> HandleResponseAsync<T>(this HttpResponseMessage response)
    {
        if (!response.IsSuccessStatusCode)
        {
            switch (response.StatusCode)
            {
                case HttpStatusCode.BadRequest:
                case HttpStatusCode.MethodNotAllowed:
                case HttpStatusCode.NotFound:
                case HttpStatusCode.NotAcceptable:
                case HttpStatusCode.Conflict:
                case HttpStatusCode.Gone:
                case HttpStatusCode.LengthRequired:
                case HttpStatusCode.PreconditionFailed:
                case HttpStatusCode.RequestEntityTooLarge:
                case HttpStatusCode.RequestUriTooLong:
                case HttpStatusCode.UnsupportedMediaType:
                case HttpStatusCode.RequestedRangeNotSatisfiable:
                case HttpStatusCode.ExpectationFailed:
                case HttpStatusCode.MisdirectedRequest:
                case HttpStatusCode.UnprocessableEntity:
                case HttpStatusCode.Locked:
                case HttpStatusCode.FailedDependency:
                case HttpStatusCode.UpgradeRequired:
                case HttpStatusCode.PreconditionRequired:
                case HttpStatusCode.RequestHeaderFieldsTooLarge:
                case HttpStatusCode.HttpVersionNotSupported:
                    throw new AIException(
                        AIException.ErrorCodes.InvalidRequest,
                        $"The request is not valid, HTTP status: {response.StatusCode:G}");

                case HttpStatusCode.Unauthorized:
                case HttpStatusCode.Forbidden:
                case HttpStatusCode.ProxyAuthenticationRequired:
                case HttpStatusCode.UnavailableForLegalReasons:
                case HttpStatusCode.NetworkAuthenticationRequired:
                    throw new AIException(
                        AIException.ErrorCodes.AccessDenied,
                        $"The request is not authorized, HTTP status: {response.StatusCode:G}");

                case HttpStatusCode.RequestTimeout:
                    throw new AIException(
                        AIException.ErrorCodes.RequestTimeout,
                        $"The request timed out, HTTP status: {response.StatusCode:G}");

                case HttpStatusCode.TooManyRequests:
                    throw new AIException(
                        AIException.ErrorCodes.Throttling,
                        $"Too many requests, HTTP status: {response.StatusCode:G}");

                case HttpStatusCode.InternalServerError:
                case HttpStatusCode.NotImplemented:
                case HttpStatusCode.BadGateway:
                case HttpStatusCode.ServiceUnavailable:
                case HttpStatusCode.GatewayTimeout:
                case HttpStatusCode.InsufficientStorage:
                    throw new AIException(
                        AIException.ErrorCodes.ServiceError,
                        $"The service failed to process the request, HTTP status: {response.StatusCode:G}");

                default:
                    throw new AIException(
                        AIException.ErrorCodes.UnknownError,
                        $"Unexpected HTTP response, status: {response.StatusCode:G}");
            }
        }

        try
        {
            var responseJson = await response.Content.ReadAsStringAsync();

            var result = Json.Deserialize<T>(responseJson);

            if (result == null)
            {
                throw new AIException(
                    AIException.ErrorCodes.InvalidResponseContent,
                    "Response JSON parse error");
            }

            return result;
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }
}
