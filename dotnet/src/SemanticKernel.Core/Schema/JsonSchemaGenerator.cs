// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130


/// <summary>
/// Class for generating JSON Schema from a type.
/// </summary>
public static class JsonSchemaGenerator
{
    /// <summary>
    /// Generate a JSON Schema from a type.
    /// </summary>
    /// <param name="type">Type to generate the JSON schema for</param>
    /// <param name="description">Description to use when generating the schema</param>
    public static JsonDocument? GenerateSchema(Type type, string description)
    {
        return GetJsonSchemaGenerator().GenerateSchema(type, description);
    }

    /// <summary>
    /// Set the JSON Schema generator.
    /// </summary>
    /// <param name="jsonSchemaGenerator"></param>
    public static void SetJsonSchemaGenerator(IJsonSchemaGenerator jsonSchemaGenerator)
    {
        Verify.NotNull(jsonSchemaGenerator);

        s_jsonSchemaGenerator = jsonSchemaGenerator;
        s_jsonSchemaGeneratorInitialized = true;
    }

    #region private
    private const string FunctionsJsonSchemaAssemblyName = "Microsoft.SemanticKernel.Functions.JsonSchema";
    private const string FunctionsJsonSchemaGeneratorTypeName = "FunctionsJsonSchemaGenerator";
    private static bool s_jsonSchemaGeneratorInitialized = false;
    private static IJsonSchemaGenerator? s_jsonSchemaGenerator;

    private static IJsonSchemaGenerator GetJsonSchemaGenerator()
    {
        if (!s_jsonSchemaGeneratorInitialized)
        {
            s_jsonSchemaGeneratorInitialized = true;
            try
            {
                var assembly = Assembly.Load(FunctionsJsonSchemaAssemblyName);

                var type = assembly.ExportedTypes.Single(type =>
                    type.Name.Equals(FunctionsJsonSchemaGeneratorTypeName, StringComparison.Ordinal) &&
                    type.GetInterface(nameof(IJsonSchemaGenerator)) is not null);

                var constructor = type.GetConstructor(Array.Empty<Type>());
                if (constructor is not null)
                {
                    s_jsonSchemaGenerator = (IJsonSchemaGenerator)constructor.Invoke(null);
                }
            }
            catch (Exception ex) when (!ex.IsCriticalException())
            {
                // Default to the null generator if default cannot be loaded and no alternative is provided
            }
        }

        s_jsonSchemaGenerator ??= new NullJsonSchemaGenerator();
        return s_jsonSchemaGenerator;
    }

    private class NullJsonSchemaGenerator : IJsonSchemaGenerator
    {
        public JsonDocument? GenerateSchema(Type type, string description) => null;
    }
    #endregion
}
