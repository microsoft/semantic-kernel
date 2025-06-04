// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Serializes an exception as a string. This is useful when serializing an instance of an exception directly or indirectly via serializing an instance that
/// references an exception. For example, when serializing chat history that contains FunctionCallContent or FunctionResultContent items referencing an exception.
/// Serializing an exception without this converter will throw a System.NotSupportedException: Serialization and deserialization of System.Reflection.MethodBase instances is not supported. Path: $.Items.Exception.TargetSite.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class ExceptionJsonConverter : JsonConverter<object>
{
    private const string ClassNamePropertyName = "className";
    private const string MessagePropertyName = "message";
    private const string InnerExceptionPropertyName = "innerException";
    private const string StackTracePropertyName = "stackTraceString";

    /// <inheritdoc/>
    public override bool CanConvert(Type typeToConvert)
    {
        return typeof(Exception).IsAssignableFrom(typeToConvert);
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, object value, JsonSerializerOptions options)
    {
        if (value is Exception ex)
        {
            writer.WriteStartObject();
            writer.WriteString(ClassNamePropertyName, ex.GetType().ToString());
            writer.WriteString(MessagePropertyName, ex.Message);
            if (ex.InnerException is Exception innerEx)
            {
                writer.WritePropertyName(InnerExceptionPropertyName);
                this.Write(writer, innerEx, options);
            }

            writer.WriteString(StackTracePropertyName, ex.StackTrace);
            writer.WriteEndObject();
        }
    }

    /// <inheritdoc/>
    public override object? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        throw new NotImplementedException();
    }
}
