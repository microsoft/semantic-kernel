// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;

namespace JsonSchemaMapper;

[EditorBrowsable(EditorBrowsableState.Never)]
internal static class JsonSchemaConstants
{
    internal const string SchemaPropertyName = "$schema";
    internal const string RefPropertyName = "$ref";
    internal const string CommentPropertyName = "$comment";
    internal const string TitlePropertyName = "title";
    internal const string DescriptionPropertyName = "description";
    internal const string TypePropertyName = "type";
    internal const string FormatPropertyName = "format";
    internal const string PatternPropertyName = "pattern";
    internal const string PropertiesPropertyName = "properties";
    internal const string RequiredPropertyName = "required";
    internal const string ItemsPropertyName = "items";
    internal const string AdditionalPropertiesPropertyName = "additionalProperties";
    internal const string EnumPropertyName = "enum";
    internal const string NotPropertyName = "not";
    internal const string AnyOfPropertyName = "anyOf";
    internal const string ConstPropertyName = "const";
    internal const string DefaultPropertyName = "default";
    internal const string MinLengthPropertyName = "minLength";
    internal const string MaxLengthPropertyName = "maxLength";
}
