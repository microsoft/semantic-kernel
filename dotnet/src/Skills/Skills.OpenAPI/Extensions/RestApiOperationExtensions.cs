// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Skills.OpenAPI.Model;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods for the <see cref="RestApiOperation"/> class.
/// </summary>
internal static class RestApiOperationExtensions
{
    /// <summary>
    /// Returns list of REST API operation parameters.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="serverUrlOverride">The server URL override.</param>
    /// <param name="addPayloadParamsFromMetadata">Determines whether to include the operation payload parameters from payload metadata.
    /// If false, the 'payload' and 'content-type' artificial parameters are added instead.
    /// </param>
    /// <param name="namespaceOperationPayloadParams">Determines whether parameter names are augmented with namespaces.
    /// Namespaces are created by prefixing parameter names with their root parameter names.
    /// For instance, without namespaces, the 'email' parameter for both the 'sender' and 'receiver' parent parameters
    /// would be resolved from the same 'email' argument, which is incorrect. However, by employing namespaces,
    /// the parameters 'sender.email' and 'receiver.mail' will be correctly resolved from arguments with the same names.
    /// </param>
    /// <returns>The list of parameters.</returns>
    public static IReadOnlyList<RestApiOperationParameter> GetParameters(this RestApiOperation operation, Uri? serverUrlOverride = null, bool addPayloadParamsFromMetadata = false, bool namespaceOperationPayloadParams = false)
    {
        var parameters = new List<RestApiOperationParameter>(operation.Parameters)
        {
            // Register the "server-url" parameter if override is provided
            new RestApiOperationParameter(
                RestApiOperation.ServerUrlArgumentName,
                "string",
                false,
                RestApiOperationParameterLocation.Path,
                RestApiOperationParameterStyle.Simple,
                defaultValue: serverUrlOverride?.AbsoluteUri ?? operation.ServerUrl?.AbsoluteUri)
        };

        //Add payload parameters
        if (operation.Method == HttpMethod.Put || operation.Method == HttpMethod.Post)
        {
            parameters.AddRange(GetPayloadParameters(operation, addPayloadParamsFromMetadata, namespaceOperationPayloadParams));
        }

        // Create a property alternative name without special symbols that are not supported by SK template language.
        foreach (var parameter in parameters)
        {
            parameter.AlternativeName = s_invalidSymbolsRegex.Replace(parameter.Name, "_");
        }

        return parameters;
    }

    /// <summary>
    /// Retrieves the payload parameters for a given REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation to retrieve parameters for.</param>
    /// <param name="useParametersFromMetadata">Flag indicating whether to include parameters from metadata.
    /// If false or not specified, the 'payload' and 'content-type' parameters are added instead.</param>
    /// <param name="namespacePayloadParamNames">Flag indicating whether to namespace payload parameter names.</param>
    /// <returns>A list of <see cref="RestApiOperationParameter"/> representing the payload parameters.</returns>
    private static List<RestApiOperationParameter> GetPayloadParameters(RestApiOperation operation, bool useParametersFromMetadata, bool namespacePayloadParamNames)
    {
        if (useParametersFromMetadata is true)
        {
            if (operation.Payload is null)
            {
                throw new SKException($"Payload parameters cannot be retrieved from the '{operation.Id}' operation payload metadata because it is missing.");
            }

            // The 'text/plain' content type payload metadata does not contain parameter names.
            // So, returning artificial 'payload' parameter instead.
            if (operation.Payload.MediaType == MediaTypeTextPlain)
            {
                return new List<RestApiOperationParameter> { CreatePayloadArtificialParameter(operation) };
            }

            return GetParametersFromPayloadMetadata(operation.Payload, namespacePayloadParamNames);
        }

        //Adding artificial 'payload' and 'content-type' in case parameters from payload metadata are not required.
        return new List<RestApiOperationParameter> {
            CreatePayloadArtificialParameter(operation),
            CreateContentTypeArtificialParameter(operation)
        };
    }

    /// <summary>
    /// Creates artificial 'content-type' parameter for a REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <returns>The 'content-type' artificial parameter.</returns>
    private static RestApiOperationParameter CreateContentTypeArtificialParameter(RestApiOperation operation)
    {
        return new RestApiOperationParameter(
            RestApiOperation.ContentTypeArgumentName,
            "string",
            false,
            RestApiOperationParameterLocation.Body,
            RestApiOperationParameterStyle.Simple,
            description: "Content type of REST API request body.");
    }

    /// <summary>
    /// Creates the 'payload' artificial parameter for a REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <returns>The 'payload' artificial parameter.</returns>
    private static RestApiOperationParameter CreatePayloadArtificialParameter(RestApiOperation operation)
    {
        return new RestApiOperationParameter(
            RestApiOperation.PayloadArgumentName,
            operation.Payload?.MediaType == MediaTypeTextPlain ? "string" : "object",
            true,
            RestApiOperationParameterLocation.Body,
            RestApiOperationParameterStyle.Simple,
            description: operation.Payload?.Description ?? "REST API request body.");
    }

    /// <summary>
    /// Retrieves parameters from the metadata of a REST API operation payload metadata.
    /// </summary>
    /// <param name="payload">The REST API operation payload.</param>
    /// <param name="namespaceParamNames">Determines whether property names are augmented with namespaces.
    /// Namespaces are created by prefixing property names with their root property names.
    /// </param>
    /// <returns>The list of payload parameters.</returns>
    private static List<RestApiOperationParameter> GetParametersFromPayloadMetadata(RestApiOperationPayload payload, bool namespaceParamNames = false)
    {
        List<RestApiOperationParameter> RetrieveLeafAndArrayProperties(IList<RestApiOperationPayloadProperty> properties, string? rootPropertyName = null)
        {
            var parameters = new List<RestApiOperationParameter>();

            foreach (var property in properties)
            {
                var parameterName = GetPropertyName(property, rootPropertyName, namespaceParamNames);

                if (!property.Properties.Any())
                {
                    parameters.Add(new RestApiOperationParameter(
                        parameterName,
                        property.Type,
                        property.IsRequired,
                        RestApiOperationParameterLocation.Body,
                        RestApiOperationParameterStyle.Simple,
                        description: property.Description));
                }

                parameters.AddRange(RetrieveLeafAndArrayProperties(property.Properties, parameterName));
            }

            return parameters;
        }

        return RetrieveLeafAndArrayProperties(payload.Properties);
    }

    /// <summary>
    /// Gets the property name based on the provided parameters.
    /// </summary>
    /// <param name="property">The property.</param>
    /// <param name="rootPropertyName">The root property name to be used for constructing the full property name.</param>
    /// <param name="namespaceProperty">Determines whether to add namespace to property name or not.</param>
    /// <returns>The property name.</returns>
    private static string GetPropertyName(RestApiOperationPayloadProperty property, string? rootPropertyName, bool namespaceProperty = false)
    {
        if (namespaceProperty is true)
        {
            return string.IsNullOrEmpty(rootPropertyName) ? property.Name : $"{rootPropertyName}.{property.Name}";
        }

        return property.Name;
    }

    private const string MediaTypeTextPlain = "text/plain";
    private static readonly Regex s_invalidSymbolsRegex = new("[^0-9A-Za-z_]+");
}
