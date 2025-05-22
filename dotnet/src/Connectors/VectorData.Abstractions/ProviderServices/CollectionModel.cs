// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a record in a vector store collection.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public sealed class CollectionModel
{
    private readonly Type _recordType;
    private readonly IRecordCreator _recordCreator;

    private KeyPropertyModel? _singleKeyProperty;
    private VectorPropertyModel? _singleVectorProperty;
    private DataPropertyModel? _singleFullTextSearchProperty;

    /// <summary>
    /// Gets the key properties of the record.
    /// </summary>
    public IReadOnlyList<KeyPropertyModel> KeyProperties { get; }

    /// <summary>
    /// Gets the data properties of the record.
    /// </summary>
    public IReadOnlyList<DataPropertyModel> DataProperties { get; }

    /// <summary>
    /// Gets the vector properties of the record.
    /// </summary>
    public IReadOnlyList<VectorPropertyModel> VectorProperties { get; }

    /// <summary>
    /// Gets all properties of the record, of all types.
    /// </summary>
    public IReadOnlyList<PropertyModel> Properties { get; }

    /// <summary>
    /// Gets all properties of the record, of all types, indexed by their model name.
    /// </summary>
    public IReadOnlyDictionary<string, PropertyModel> PropertyMap { get; }

    /// <summary>
    /// Gets a value that indicates whether any of the vector properties in the model require embedding generation.
    /// </summary>
    public bool EmbeddingGenerationRequired { get; }

    internal CollectionModel(
        Type recordType,
        IRecordCreator recordCreator,
        IReadOnlyList<KeyPropertyModel> keyProperties,
        IReadOnlyList<DataPropertyModel> dataProperties,
        IReadOnlyList<VectorPropertyModel> vectorProperties,
        IReadOnlyDictionary<string, PropertyModel> propertyMap)
    {
        this._recordType = recordType;
        this._recordCreator = recordCreator;

        this.KeyProperties = keyProperties;
        this.DataProperties = dataProperties;
        this.VectorProperties = vectorProperties;
        this.PropertyMap = propertyMap;
        this.Properties = propertyMap.Values.ToList();

        this.EmbeddingGenerationRequired = vectorProperties.Any(p => p.EmbeddingType != p.Type);
    }

    /// <summary>
    /// Returns the single key property in the model, and throws if there are multiple key properties.
    /// Suitable for connectors where validation is in place for single keys only (<see cref="CollectionModelBuildingOptions.SupportsMultipleKeys"/>).
    /// </summary>
    public KeyPropertyModel KeyProperty => this._singleKeyProperty ??= this.KeyProperties.Single();

    /// <summary>
    /// Returns the single vector property in the model, and throws if there are multiple vector properties.
    /// Suitable for connectors where validation is in place for single vectors only (<see cref="CollectionModelBuildingOptions.SupportsMultipleVectors"/>).
    /// </summary>
    public VectorPropertyModel VectorProperty => this._singleVectorProperty ??= this.VectorProperties.Single();

    /// <summary>
    /// Instantiates a new record of the specified type.
    /// </summary>
    // TODO: the pattern of first instantiating via parameterless constructor and then populating the properties isn't compatible
    // with read-only types, where properties have no setters. Supporting those would be problematic given the that different
    // connectors have completely different representations of the data coming back from the database, and which needs to be
    // populated.
    public TRecord CreateRecord<TRecord>()
    {
        Debug.Assert(typeof(TRecord) == this._recordType, "Type mismatch between record type and model type.");

        return this._recordCreator.Create<TRecord>();
    }

    /// <summary>
    /// Gets the vector property with the provided name if a name is provided, and falls back
    /// to a vector property in the schema if not.
    /// </summary>
    /// <param name="searchOptions">The search options, which defines the vector property name.</param>
    /// <exception cref="InvalidOperationException"><para>The provided property name is not a valid text data property name.</para><para>OR</para><para>No name was provided and there's more than one vector property.</para></exception>
    public VectorPropertyModel GetVectorPropertyOrSingle<TRecord>(VectorSearchOptions<TRecord> searchOptions)
    {
        if (searchOptions.VectorProperty is not null)
        {
            return this.GetMatchingProperty<TRecord, VectorPropertyModel>(searchOptions.VectorProperty, data: false);
        }

        // If vector property name is not provided, check if there is a single vector property, or throw if there are no vectors or more than one.
        // TODO: Make a single switch expression + coalesce from the following - dotnet format fails on it for now
        if (this._singleVectorProperty is null)
        {
            switch (this.VectorProperties)
            {
                case [var singleProperty]:
                    this._singleVectorProperty = singleProperty;
                    break;

                case { Count: 0 }:
                    throw new InvalidOperationException($"The '{this._recordType.Name}' type does not have any vector properties.");

                default:
                    throw new InvalidOperationException($"The '{this._recordType.Name}' type has multiple vector properties, please specify your chosen property via options.");
            }
        }

        return this._singleVectorProperty;
    }

    /// <summary>
    /// Gets the text data property with the provided name that has full text search indexing enabled, or falls back
    /// to a text data property in the schema if no name is provided.
    /// </summary>
    /// <param name="expression">The full text search property selector.</param>
    /// <exception cref="InvalidOperationException"><para>The provided property name is not a valid text data property name.</para><para>OR</para><para>No name was provided and there's more than one text data property with full text search indexing enabled.</para></exception>
    public DataPropertyModel GetFullTextDataPropertyOrSingle<TRecord>(Expression<Func<TRecord, object?>>? expression)
    {
        if (expression is not null)
        {
            var property = this.GetMatchingProperty<TRecord, DataPropertyModel>(expression, data: true);

            return property.IsFullTextIndexed
                ? property
                : throw new InvalidOperationException($"The property '{property.ModelName}' on '{this._recordType.Name}' must have full text search indexing enabled.");
        }

        if (this._singleFullTextSearchProperty is null)
        {
            // If text data property name is not provided, check if a single full text indexed text property exists or throw otherwise.
            var fullTextStringProperties = this.DataProperties
                .Where(l => l.Type == typeof(string) && l.IsFullTextIndexed)
                .ToList();

            // If text data property name is not provided, check if a single full text indexed text property exists or throw otherwise.
            switch (fullTextStringProperties)
            {
                // If there is a single property, use it.
                // If there are no properties, throw.
                // If there are multiple properties, throw.
                case [var singleProperty]:
                    this._singleFullTextSearchProperty = singleProperty;
                    break;

                case { Count: 0 }:
                    throw new InvalidOperationException($"The '{this._recordType.Name}' type does not have any text data properties that have full text indexing enabled.");

                default:
                    throw new InvalidOperationException($"The '{this._recordType.Name}' type has multiple text data properties that have full text indexing enabled, please specify your chosen property via options.");
            }
        }

        return this._singleFullTextSearchProperty;
    }

    /// <summary>
    /// Gets the data or key property selected by the provided expression.
    /// </summary>
    /// <param name="expression">The property selector.</param>
    /// <exception cref="InvalidOperationException">The provided property name is not a valid data or key property name.</exception>
    public PropertyModel GetDataOrKeyProperty<TRecord>(Expression<Func<TRecord, object?>> expression)
        => this.GetMatchingProperty<TRecord, PropertyModel>(expression, data: true);

    private TProperty GetMatchingProperty<TRecord, TProperty>(Expression<Func<TRecord, object?>> expression, bool data)
        where TProperty : PropertyModel
    {
        var node = expression.Body;

        // First, unwrap any object convert node: r => (object)r.PropertyName becomes r => r.PropertyName
        if (expression.Body is UnaryExpression { NodeType: ExpressionType.Convert } convert
            && convert.Type == typeof(object))
        {
            node = convert.Operand;
        }

        var propertyName = node switch
        {
            // Simple member expression over the lambda parameter (r => r.PropertyName)
            MemberExpression { Member: PropertyInfo clrProperty } member when member.Expression == expression.Parameters[0]
                => clrProperty.Name,

            // Dictionary access over the lambda parameter, in dynamic mapping (r => r["PropertyName"])
            MethodCallExpression { Method.Name: "get_Item", Arguments: [var keyExpression] } methodCall
                => keyExpression switch
                {
                    ConstantExpression { Value: string text } => text,
                    MemberExpression field when TryGetCapturedValue(field, out object? capturedValue) && capturedValue is string text => text,
                    _ => throw new InvalidOperationException("Invalid dictionary key expression")
                },

            _ => throw new InvalidOperationException("Property selector lambda is invalid")
        };

        if (!this.PropertyMap.TryGetValue(propertyName, out var property))
        {
            throw new InvalidOperationException($"Property '{propertyName}' could not be found.");
        }

        return property is TProperty typedProperty
            ? typedProperty
            : throw new InvalidOperationException($"Property '{propertyName}' isn't of type '{typeof(TProperty).Name}'.");

        static bool TryGetCapturedValue(Expression expression, out object? capturedValue)
        {
            if (expression is MemberExpression { Expression: ConstantExpression constant, Member: FieldInfo fieldInfo }
                && constant.Type.Attributes.HasFlag(TypeAttributes.NestedPrivate)
                && Attribute.IsDefined(constant.Type, typeof(CompilerGeneratedAttribute), inherit: true))
            {
                capturedValue = fieldInfo.GetValue(constant.Value);
                return true;
            }

            capturedValue = null;
            return false;
        }
    }
}
