// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Net;
using System.Text.Json;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.Extensions;

/// <summary>
/// HTTP Client extensions.
/// </summary>
public static class HttpClientExtensions
{
    /// <summary>
    /// Sends HTTP request and handles response.
    /// </summary>
    /// <param name="httpClient">Instance of <see cref="HttpClient"/> to send request.</param>
    /// <param name="httpRequestMessage">Instance of <see cref="HttpRequestMessage"/> to send.</param>
    /// <returns>Returns deserialized response.</returns>
    public static async Task<T> SendRequestAsync<T>(this HttpClient httpClient, HttpRequestMessage httpRequestMessage)
    {
        string responseJson;

        try
        {
            HttpResponseMessage response = await httpClient.SendAsync(httpRequestMessage).ConfigureAwait(false);

            if (response == null)
            {
                throw new AIException(AIException.ErrorCodes.NoResponse, "Empty response");
            }

            ValidateResponse(response);

            responseJson = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }

        return DeserializeResponse<T>(responseJson);
    }

    #region private ================================================================================

    /// <summary>
    /// Validates response based on HTTP status code.
    /// </summary>
    /// <param name="response">Instance of <see cref="HttpResponseMessage"/> to validate.</param>
    private static void ValidateResponse(HttpResponseMessage response)
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
    }

    /// <summary>
    /// Returns deserialized response.
    /// </summary>
    /// <param name="responseJson">JSON string to deserialize.</param>
    private static T DeserializeResponse<T>(string responseJson)
    {
        try
        {
            var result = JsonSerializer.Deserialize<T>(responseJson);

            if (result != null)
            {
                return result;
            }

            throw new AIException(
                AIException.ErrorCodes.InvalidResponseContent,
                "Response JSON parse error");
        }
        catch (Exception e) when (e is not AIException)
        {
            throw new AIException(
                AIException.ErrorCodes.UnknownError,
                $"Something went wrong: {e.Message}", e);
        }
    }

    #endregion
}
