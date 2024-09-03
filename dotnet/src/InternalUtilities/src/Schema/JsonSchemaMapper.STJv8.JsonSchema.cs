// Copyright (c) Microsoft. All rights reserved.

#if !NET9_0_OR_GREATER && !SYSTEM_TEXT_JSON_V9
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Text.Json.Nodes;

namespace JsonSchemaMapper;

#if EXPOSE_JSON_SCHEMA_MAPPER
public
#else
internal
#endif
    static partial class JsonSchemaMapper
{
    // Simple JSON schema representation taken from System.Text.Json
    // https://github.com/dotnet/runtime/blob/50d6cad649aad2bfa4069268eddd16fd51ec5cf3/src/libraries/System.Text.Json/src/System/Text/Json/Schema/JsonSchema.cs
    private sealed class JsonSchema
    {
        public static JsonSchema False { get; } = new(false);
        public static JsonSchema True { get; } = new(true);

        public JsonSchema()
        {
        }

        private JsonSchema(bool trueOrFalse)
        {
            _trueOrFalse = trueOrFalse;
        }

        public bool IsTrue => _trueOrFalse is true;
        public bool IsFalse => _trueOrFalse is false;
        private readonly bool? _trueOrFalse;

        public string? Schema
        {
            get => _schema;
            set
            {
                VerifyMutable();
                _schema = value;
            }
        }

        private string? _schema;

        public string? Title
        {
            get => _title;
            set
            {
                VerifyMutable();
                _title = value;
            }
        }

        private string? _title;

        public string? Description
        {
            get => _description;
            set
            {
                VerifyMutable();
                _description = value;
            }
        }

        private string? _description;

        public string? Ref
        {
            get => _ref;
            set
            {
                VerifyMutable();
                _ref = value;
            }
        }

        private string? _ref;

        public string? Comment
        {
            get => _comment;
            set
            {
                VerifyMutable();
                _comment = value;
            }
        }

        private string? _comment;

        public JsonSchemaType Type
        {
            get => _type;
            set
            {
                VerifyMutable();
                _type = value;
            }
        }

        private JsonSchemaType _type = JsonSchemaType.Any;

        public string? Format
        {
            get => _format;
            set
            {
                VerifyMutable();
                _format = value;
            }
        }

        private string? _format;

        public string? Pattern
        {
            get => _pattern;
            set
            {
                VerifyMutable();
                _pattern = value;
            }
        }

        private string? _pattern;

        public JsonNode? Constant
        {
            get => _constant;
            set
            {
                VerifyMutable();
                _constant = value;
            }
        }

        private JsonNode? _constant;

        public List<KeyValuePair<string, JsonSchema>>? Properties
        {
            get => _properties;
            set
            {
                VerifyMutable();
                _properties = value;
            }
        }

        private List<KeyValuePair<string, JsonSchema>>? _properties;

        public List<string>? Required
        {
            get => _required;
            set
            {
                VerifyMutable();
                _required = value;
            }
        }

        private List<string>? _required;

        public JsonSchema? Items
        {
            get => _items;
            set
            {
                VerifyMutable();
                _items = value;
            }
        }

        private JsonSchema? _items;

        public JsonSchema? AdditionalProperties
        {
            get => _additionalProperties;
            set
            {
                VerifyMutable();
                _additionalProperties = value;
            }
        }

        private JsonSchema? _additionalProperties;

        public JsonArray? Enum
        {
            get => _enum;
            set
            {
                VerifyMutable();
                _enum = value;
            }
        }

        private JsonArray? _enum;

        public JsonSchema? Not
        {
            get => _not;
            set
            {
                VerifyMutable();
                _not = value;
            }
        }

        private JsonSchema? _not;

        public List<JsonSchema>? AnyOf
        {
            get => _anyOf;
            set
            {
                VerifyMutable();
                _anyOf = value;
            }
        }

        private List<JsonSchema>? _anyOf;

        public bool HasDefaultValue
        {
            get => _hasDefaultValue;
            set
            {
                VerifyMutable();
                _hasDefaultValue = value;
            }
        }

        private bool _hasDefaultValue;

        public JsonNode? DefaultValue
        {
            get => _defaultValue;
            set
            {
                VerifyMutable();
                _defaultValue = value;
            }
        }

        private JsonNode? _defaultValue;

        public int? MinLength
        {
            get => _minLength;
            set
            {
                VerifyMutable();
                _minLength = value;
            }
        }

        private int? _minLength;

        public int? MaxLength
        {
            get => _maxLength;
            set
            {
                VerifyMutable();
                _maxLength = value;
            }
        }

        private int? _maxLength;

        public JsonSchemaGenerationContext? GenerationContext { get; set; }

        public int KeywordCount
        {
            get
            {
                if (_trueOrFalse != null)
                {
                    return 0;
                }

                int count = 0;
                Count(Schema != null);
                Count(Ref != null);
                Count(Comment != null);
                Count(Title != null);
                Count(Description != null);
                Count(Type != JsonSchemaType.Any);
                Count(Format != null);
                Count(Pattern != null);
                Count(Constant != null);
                Count(Properties != null);
                Count(Required != null);
                Count(Items != null);
                Count(AdditionalProperties != null);
                Count(Enum != null);
                Count(Not != null);
                Count(AnyOf != null);
                Count(HasDefaultValue);
                Count(MinLength != null);
                Count(MaxLength != null);

                return count;

                void Count(bool isKeywordSpecified)
                {
                    count += isKeywordSpecified ? 1 : 0;
                }
            }
        }

        public void MakeNullable()
        {
            if (_trueOrFalse != null)
            {
                return;
            }

            if (Type != JsonSchemaType.Any)
            {
                Type |= JsonSchemaType.Null;
            }
        }

        public JsonNode ToJsonNode(JsonSchemaMapperConfiguration options)
        {
            if (_trueOrFalse is { } boolSchema)
            {
                return CompleteSchema((JsonNode)boolSchema);
            }

            var objSchema = new JsonObject();

            if (Schema != null)
            {
                objSchema.Add(JsonSchemaConstants.SchemaPropertyName, Schema);
            }

            if (Title != null)
            {
                objSchema.Add(JsonSchemaConstants.TitlePropertyName, Title);
            }

            if (Description != null)
            {
                objSchema.Add(JsonSchemaConstants.DescriptionPropertyName, Description);
            }

            if (Ref != null)
            {
                objSchema.Add(JsonSchemaConstants.RefPropertyName, Ref);
            }

            if (Comment != null)
            {
                objSchema.Add(JsonSchemaConstants.CommentPropertyName, Comment);
            }

            if (MapSchemaType(Type) is JsonNode type)
            {
                objSchema.Add(JsonSchemaConstants.TypePropertyName, type);
            }

            if (Format != null)
            {
                objSchema.Add(JsonSchemaConstants.FormatPropertyName, Format);
            }

            if (Pattern != null)
            {
                objSchema.Add(JsonSchemaConstants.PatternPropertyName, Pattern);
            }

            if (Constant != null)
            {
                objSchema.Add(JsonSchemaConstants.ConstPropertyName, Constant);
            }

            if (Properties != null)
            {
                var properties = new JsonObject();
                foreach (KeyValuePair<string, JsonSchema> property in Properties)
                {
                    properties.Add(property.Key, property.Value.ToJsonNode(options));
                }

                objSchema.Add(JsonSchemaConstants.PropertiesPropertyName, properties);
            }

            if (Required != null)
            {
                var requiredArray = new JsonArray();
                foreach (string requiredProperty in Required)
                {
                    requiredArray.Add((JsonNode)requiredProperty);
                }

                objSchema.Add(JsonSchemaConstants.RequiredPropertyName, requiredArray);
            }

            if (Items != null)
            {
                objSchema.Add(JsonSchemaConstants.ItemsPropertyName, Items.ToJsonNode(options));
            }

            if (AdditionalProperties != null)
            {
                objSchema.Add(JsonSchemaConstants.AdditionalPropertiesPropertyName, AdditionalProperties.ToJsonNode(options));
            }

            if (Enum != null)
            {
                objSchema.Add(JsonSchemaConstants.EnumPropertyName, Enum);
            }

            if (Not != null)
            {
                objSchema.Add(JsonSchemaConstants.NotPropertyName, Not.ToJsonNode(options));
            }

            if (AnyOf != null)
            {
                JsonArray anyOfArray = new();
                foreach (JsonSchema schema in AnyOf)
                {
                    anyOfArray.Add(schema.ToJsonNode(options));
                }

                objSchema.Add(JsonSchemaConstants.AnyOfPropertyName, anyOfArray);
            }

            if (HasDefaultValue)
            {
                objSchema.Add(JsonSchemaConstants.DefaultPropertyName, DefaultValue);
            }

            if (MinLength is int minLength)
            {
                objSchema.Add(JsonSchemaConstants.MinLengthPropertyName, (JsonNode)minLength);
            }

            if (MaxLength is int maxLength)
            {
                objSchema.Add(JsonSchemaConstants.MaxLengthPropertyName, (JsonNode)maxLength);
            }

            return CompleteSchema(objSchema);

            JsonNode CompleteSchema(JsonNode schema)
            {
                if (GenerationContext is { } context)
                {
                    Debug.Assert(options.TransformSchemaNode != null, "context should only be populated if a callback is present.");

                    // Apply any user-defined transformations to the schema.
                    return options.TransformSchemaNode!(context, schema);
                }

                return schema;
            }
        }

        public static void EnsureMutable(ref JsonSchema schema)
        {
            switch (schema._trueOrFalse)
            {
                case false:
                    schema = new JsonSchema { Not = JsonSchema.True };
                    break;
                case true:
                    schema = new JsonSchema();
                    break;
            }
        }

        private static readonly JsonSchemaType[] s_schemaValues = new JsonSchemaType[]
        {
        // NB the order of these values influences order of types in the rendered schema
        JsonSchemaType.String,
        JsonSchemaType.Integer,
        JsonSchemaType.Number,
        JsonSchemaType.Boolean,
        JsonSchemaType.Array,
        JsonSchemaType.Object,
        JsonSchemaType.Null,
        };

        private void VerifyMutable()
        {
            Debug.Assert(_trueOrFalse is null, "Schema is not mutable");
            if (_trueOrFalse is not null)
            {
                Throw();
                static void Throw() => throw new InvalidOperationException();
            }
        }

        private static JsonNode? MapSchemaType(JsonSchemaType schemaType)
        {
            if (schemaType is JsonSchemaType.Any)
            {
                return null;
            }

            if (ToIdentifier(schemaType) is string identifier)
            {
                return identifier;
            }

            var array = new JsonArray();
            foreach (JsonSchemaType type in s_schemaValues)
            {
                if ((schemaType & type) != 0)
                {
                    array.Add((JsonNode)ToIdentifier(type)!);
                }
            }

            return array;

            static string? ToIdentifier(JsonSchemaType schemaType)
            {
                return schemaType switch
                {
                    JsonSchemaType.Null => "null",
                    JsonSchemaType.Boolean => "boolean",
                    JsonSchemaType.Integer => "integer",
                    JsonSchemaType.Number => "number",
                    JsonSchemaType.String => "string",
                    JsonSchemaType.Array => "array",
                    JsonSchemaType.Object => "object",
                    _ => null,
                };
            }
        }
    }

    [EditorBrowsable(EditorBrowsableState.Never)]
    private enum JsonSchemaType
    {
        Any = 0, // No type declared on the schema
        Null = 1,
        Boolean = 2,
        Integer = 4,
        Number = 8,
        String = 16,
        Array = 32,
        Object = 64,
    }
}
#endif
