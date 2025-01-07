// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Class for extensions methods for the <see cref="RestApiOperation"/> class.
/// </summary>
internal static partial class RestApiOperationExtensions
{
    /// <summary>
    /// Returns list of REST API operation parameters.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="addPayloadParamsFromMetadata">Determines whether to include the operation payload parameters from payload metadata.
    /// If false, the 'payload' and 'content-type' artificial parameters are added instead.
    /// </param>
    /// <param name="enablePayloadNamespacing">Determines whether parameter names are augmented with namespaces.
    /// Namespaces are created by prefixing parameter names with their root parameter names.
    /// For instance, without namespaces, the 'email' parameter for both the 'sender' and 'receiver' parent parameters
    /// would be resolved from the same 'email' argument, which is incorrect. However, by employing namespaces,
    /// the parameters 'sender.email' and 'receiver.mail' will be correctly resolved from arguments with the same names.
    /// </param>
    /// <param name="parameterFilter">Filter which can be used to eliminate or modify RestApiParameters.</param>
    /// <returns>The list of parameters.</returns>
    public static IReadOnlyList<RestApiParameter> GetParameters(
        this RestApiOperation operation,
        bool addPayloadParamsFromMetadata = true,
        bool enablePayloadNamespacing = false,
        RestApiParameterFilter? parameterFilter = null)
    {
        var parameters = new List<RestApiParameter>(parameterFilter is null ?
        operation.Parameters :
            operation.Parameters.Select(p => parameterFilter(new(operation, p))).Where(p => p != null).Cast<RestApiParameter>().ToList());

        // Add payload parameters
        if (operation.Payload is not null)
        {
            parameters.AddRange(GetPayloadParameters(operation, addPayloadParamsFromMetadata, enablePayloadNamespacing, parameterFilter));
        }

        foreach (var parameter in parameters)
        {
            // The functionality of replacing invalid symbols and setting the argument name
            // was introduced to handle dashes allowed in OpenAPI parameter names and
            // not supported by SK at that time. More context -
            // https://github.com/microsoft/semantic-kernel/pull/283#discussion_r1156286780
            // It's kept for backward compatibility only.
            parameter.ArgumentName ??= InvalidSymbolsRegex().Replace(parameter.Name, "_");
        }

        return parameters;
    }

    /// <summary>
    /// Returns the default return parameter metadata for a given REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation object with Responses to parse.</param>
    /// <param name="preferredResponses">A list of preferred response codes to use when selecting the default response.</param>
    /// <returns>The default return parameter metadata, if any.</returns>
    public static KernelReturnParameterMetadata? GetDefaultReturnParameter(this RestApiOperation operation, string[]? preferredResponses = null)
    {
        RestApiExpectedResponse? restOperationResponse = GetDefaultResponse(operation.Responses, preferredResponses ??= s_preferredResponses);

        var returnParameter =
            restOperationResponse is not null ? new KernelReturnParameterMetadata { Description = restOperationResponse.Description, Schema = restOperationResponse.Schema } : null;

        return returnParameter;
    }

    /// <summary>
    /// Retrieves the default response.
    /// </summary>
    /// <param name="responses">Possible REST API responses.</param>
    /// <param name="preferredResponses">The preferred response codes to use when selecting the default response.</param>
    /// <returns>The default response, if any.</returns>
    private static RestApiExpectedResponse? GetDefaultResponse(IDictionary<string, RestApiExpectedResponse> responses, string[] preferredResponses)
    {
        foreach (var code in preferredResponses)
        {
            if (responses.TryGetValue(code, out var response))
            {
                return response;
            }
        }

        // If no appropriate response is found, return null or throw an exception
        return null;
    }

    /// <summary>
    /// Retrieves the payload parameters for a given REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation to retrieve parameters for.</param>
    /// <param name="useParametersFromMetadata">Flag indicating whether to include parameters from metadata.
    /// If false or not specified, the 'payload' and 'content-type' parameters are added instead.</param>
    /// <param name="enableNamespacing">Flag indicating whether to namespace payload parameter names.</param>
    /// <param name="parameterFilter">Filter which can be used to eliminate or modify RestApiParameters.</param>
    /// <returns>A list of <see cref="RestApiParameter"/> representing the payload parameters.</returns>
    private static List<RestApiParameter> GetPayloadParameters(RestApiOperation operation, bool useParametersFromMetadata, bool enableNamespacing, RestApiParameterFilter? parameterFilter)
    {
        if (useParametersFromMetadata)
        {
            if (operation.Payload is null)
            {
                throw new KernelException($"Payload parameters cannot be retrieved from the '{operation.Id}' operation payload metadata because it is missing.");
            }

            // The 'text/plain' content type payload metadata does not contain parameter names.
            // So, returning artificial 'payload' parameter instead.
            if (operation.Payload.MediaType == MediaTypeTextPlain)
            {
                return [CreatePayloadArtificialParameter(operation)];
            }

            return GetParametersFromPayloadMetadata(operation, operation.Payload, operation.Payload.Properties, enableNamespacing, parameterFilter);
        }

        // Adding artificial 'payload' and 'content-type' in case parameters from payload metadata are not required.
        if (parameterFilter is not null)
        {
            return new RestApiParameter[]
            {
                CreatePayloadArtificialParameter(operation),
                CreateContentTypeArtificialParameter(operation)
            }.Where(p => parameterFilter(new(operation, p)) is not null).ToList();
        }
        return
        [
            CreatePayloadArtificialParameter(operation),
            CreateContentTypeArtificialParameter(operation)
        ];
    }

    /// <summary>
    /// Creates the 'content-type' artificial parameter for a REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <returns>The 'content-type' artificial parameter.</returns>
    private static RestApiParameter CreateContentTypeArtificialParameter(RestApiOperation operation)
    {
        return new RestApiParameter(
            RestApiOperation.ContentTypeArgumentName,
            "string",
            isRequired: false,
            expand: false,
            RestApiParameterLocation.Body,
            RestApiParameterStyle.Simple,
            description: "Content type of REST API request body.");
    }

    /// <summary>
    /// Creates the 'payload' artificial parameter for a REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <returns>The 'payload' artificial parameter.</returns>
    private static RestApiParameter CreatePayloadArtificialParameter(RestApiOperation operation)
    {
        return new RestApiParameter(
            RestApiOperation.PayloadArgumentName,
            operation.Payload?.MediaType == MediaTypeTextPlain ? "string" : "object",
            isRequired: true,
            expand: false,
            RestApiParameterLocation.Body,
            RestApiParameterStyle.Simple,
            description: operation.Payload?.Description ?? "REST API request body.",
            schema: operation.Payload?.Schema);
    }

    /// <summary>
    /// Retrieves parameters from REST API payload metadata.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="parent">The parent object of the parameter, can be either an instance of <see cref="RestApiPayload"/> or <see cref="RestApiPayloadProperty"/>.</param>
    /// <param name="properties">The REST API payload properties.</param>
    /// <param name="enableNamespacing">Determines whether property names are augmented with namespaces.
    /// Namespaces are created by prefixing property names with their root property names.
    /// </param>
    /// <param name="parameterFilter">Filter which can be used to eliminate or modify RestApiParameters.</param>
    /// <param name="rootPropertyName">The root property name.</param>
    /// <returns>The list of payload parameters.</returns>
    private static List<RestApiParameter> GetParametersFromPayloadMetadata(RestApiOperation operation, object parent, IList<RestApiPayloadProperty> properties, bool enableNamespacing = false, RestApiParameterFilter? parameterFilter = null, string? rootPropertyName = null)
    {
        var parameters = new List<RestApiParameter>();

        foreach (var property in properties)
        {
            var parameterName = GetPropertyName(property, rootPropertyName, enableNamespacing);

            if (!property.Properties.Any())
            {
                // Assign an argument name (sanitized form of the property name) so that the parameter value look-up / resolution functionality in the RestApiOperationRunner
                // class can find the value for the parameter by the argument name in the arguments dictionary. If the argument name is not assigned here, the resolution mechanism
                // will try to find the parameter value by the parameter's original name. However, because the parameter was advertised with the sanitized name by the RestApiOperationExtensions.GetParameters
                // method, no value will be found, and an exception will be thrown: "No argument is found for the 'customerid_contact@odata.bind' payload property."
                property.ArgumentName ??= InvalidSymbolsRegex().Replace(parameterName, "_");

                var parameter = new RestApiParameter(
                    name: parameterName,
                    type: property.Type,
                    isRequired: property.IsRequired,
                    expand: false,
                    location: RestApiParameterLocation.Body,
                    style: RestApiParameterStyle.Simple,
                    defaultValue: property.DefaultValue,
                    description: property.Description,
                    format: property.Format,
                    schema: property.Schema)
                {
                    ArgumentName = property.ArgumentName
                };
                parameter = parameterFilter is null ? parameter : parameterFilter(new(operation, parameter) { Parent = parent });
                if (parameter is not null)
                {
                    parameters.Add(parameter);
                }
            }

            parameters.AddRange(GetParametersFromPayloadMetadata(operation, property, property.Properties, enableNamespacing, parameterFilter, parameterName));
        }

        return parameters;
    }

    /// <summary>
    /// Gets the property name based on the provided parameters.
    /// </summary>
    /// <param name="property">The property.</param>
    /// <param name="rootPropertyName">The root property name to be used for constructing the full property name.</param>
    /// <param name="enableNamespacing">Determines whether to add namespace to property name or not.</param>
    /// <returns>The property name.</returns>
    private static string GetPropertyName(RestApiPayloadProperty property, string? rootPropertyName, bool enableNamespacing = false)
    {
        if (enableNamespacing)
        {
            return string.IsNullOrEmpty(rootPropertyName) ? property.Name : $"{rootPropertyName}.{property.Name}";
        }

        return property.Name;
    }

    private const string MediaTypeTextPlain = "text/plain";
    private static readonly string[] s_preferredResponses = ["200", "201", "202", "203", "204", "205", "206", "207", "208", "226", "2XX", "default"];

#if NET
    [GeneratedRegex("[^0-9A-Za-z_]+")]
    private static partial Regex InvalidSymbolsRegex();
#else
    private static Regex InvalidSymbolsRegex() => s_invalidSymbolsRegex;
    private static readonly Regex s_invalidSymbolsRegex = new("[^0-9A-Za-z_]+", RegexOptions.Compiled);
#endif
}
