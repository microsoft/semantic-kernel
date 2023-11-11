// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Schema;

/// <summary>
/// Class for generating JSON Schema from a type.
/// </summary>
public static class JsonSchemaGenerator
{
    /// <summary>
    /// Generate a JSON Schema from a type.
    /// </summary>
    /// <param name="type"></param>
    /// <param name="description"></param>
    public static JsonDocument? GenerateSchema(Type type, string description)
    {
        return GetJsonSchemaGenerator().GenerateSchema(type, description);
    }

    #region private
    private static IJsonSchemaGenerator? s_jsonSchemaGenerator;

    private static IJsonSchemaGenerator GetJsonSchemaGenerator()
    {
        if (s_jsonSchemaGenerator == null)
        {
            var appDomain = AppDomain.CurrentDomain;
            var assemblies = appDomain.GetAssemblies();
            var type = typeof(IJsonSchemaGenerator);
            var types = assemblies.SelectMany(a => a.GetTypes())
                .Where(t => type.IsAssignableFrom(t)
                    && t.IsClass
                    && !t.IsAbstract
                    && t.IsPublic
                    && t.GetConstructor(Array.Empty<Type>()) != null);
            var t = types.FirstOrDefault();
            s_jsonSchemaGenerator = t is not null ? (IJsonSchemaGenerator)Activator.CreateInstance(t) : new NullJsonSchemaGenerator();
        }

        return s_jsonSchemaGenerator;
    }

    private class NullJsonSchemaGenerator : IJsonSchemaGenerator
    {
        public JsonDocument? GenerateSchema(Type type, string description) => null;
    }
    #endregion
}
