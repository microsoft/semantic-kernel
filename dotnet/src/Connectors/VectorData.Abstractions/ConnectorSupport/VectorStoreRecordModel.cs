// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// A model representing a record in a vector store collection.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public sealed class VectorStoreRecordModel
{
    [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicParameterlessConstructor)]
    private readonly Type _recordType;

    private VectorStoreRecordKeyPropertyModel? _singleKeyProperty;
    private VectorStoreRecordVectorPropertyModel? _singleVectorProperty;
    private VectorStoreRecordDataPropertyModel? _singleFullTextSearchProperty;

    /// <summary>
    /// The key properties of the record.
    /// </summary>
    public IReadOnlyList<VectorStoreRecordKeyPropertyModel> KeyProperties { get; }

    /// <summary>
    /// The data properties of the record.
    /// </summary>
    public IReadOnlyList<VectorStoreRecordDataPropertyModel> DataProperties { get; }

    /// <summary>
    /// The vector properties of the record.
    /// </summary>
    public IReadOnlyList<VectorStoreRecordVectorPropertyModel> VectorProperties { get; }

    /// <summary>
    /// All properties of the record, of all types.
    /// </summary>
    public IReadOnlyList<VectorStoreRecordPropertyModel> Properties { get; }

    /// <summary>
    /// All properties of the record, of all types, indexed by their model name.
    /// </summary>
    public IReadOnlyDictionary<string, VectorStoreRecordPropertyModel> PropertyMap { get; }

    internal VectorStoreRecordModel(
        Type recordType,
        IReadOnlyList<VectorStoreRecordKeyPropertyModel> keyProperties,
        IReadOnlyList<VectorStoreRecordDataPropertyModel> dataProperties,
        IReadOnlyList<VectorStoreRecordVectorPropertyModel> vectorProperties,
        IReadOnlyDictionary<string, VectorStoreRecordPropertyModel> propertyMap)
    {
        this._recordType = recordType;
        this.KeyProperties = keyProperties;
        this.DataProperties = dataProperties;
        this.VectorProperties = vectorProperties;
        this.PropertyMap = propertyMap;
        this.Properties = propertyMap.Values.ToList();
    }

    /// <summary>
    /// Returns the single key property in the model, and throws if there are multiple key properties.
    /// Suitable for connectors where validation is in place for single keys only (<see cref="VectorStoreRecordModelBuildingOptions.SupportsMultipleKeys"/>).
    /// </summary>
    public VectorStoreRecordKeyPropertyModel KeyProperty => this._singleKeyProperty ??= this.KeyProperties.Single();

    /// <summary>
    /// Returns the single vector property in the model, and throws if there are multiple vector properties.
    /// Suitable for connectors where validation is in place for single vectors only (<see cref="VectorStoreRecordModelBuildingOptions.SupportsMultipleVectors"/>).
    /// </summary>
    public VectorStoreRecordVectorPropertyModel VectorProperty => this._singleVectorProperty ??= this.VectorProperties.Single();

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

        return Activator.CreateInstance<TRecord>() ?? throw new InvalidOperationException($"Failed to instantiate record of type '{typeof(TRecord).Name}'.");
    }

    /// <summary>
    /// Get the vector property with the provided name if a name is provided, and fall back
    /// to a vector property in the schema if not. If no name is provided and there is more
    /// than one vector property, an exception will be thrown.
    /// </summary>
    /// <param name="searchOptions">The search options.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided property name is not a valid vector property name.</exception>
    public VectorStoreRecordVectorPropertyModel GetVectorPropertyOrSingle<TRecord>(VectorSearchOptions<TRecord>? searchOptions)
    {
        if (searchOptions is not null)
        {
#pragma warning disable CS0618 // Type or member is obsolete
            string? vectorPropertyName = searchOptions.VectorPropertyName;
#pragma warning restore CS0618 // Type or member is obsolete

            // If vector property name is provided, try to find it in schema or throw an exception.
            if (!string.IsNullOrWhiteSpace(vectorPropertyName))
            {
                // Check vector properties by data model property name.
                return this.VectorProperties.FirstOrDefault(p => p.ModelName == vectorPropertyName)
                    ?? throw new InvalidOperationException($"The {this._recordType.FullName} type does not have a vector property named '{vectorPropertyName}'.");
            }
            else if (searchOptions.VectorProperty is Expression<Func<TRecord, object?>> expression)
            {
                return this.GetMatchingProperty<TRecord, VectorStoreRecordVectorPropertyModel>(expression, data: false);
            }
        }

        // If vector property name is not provided, check if there is a single vector property, or throw if there are no vectors or more than one.
        return this._singleVectorProperty ??= this.VectorProperties switch
        {
            [var singleProperty] => singleProperty,
            { Count: 0 } => throw new InvalidOperationException($"The '{this._recordType.Name}' type does not have any vector properties."),
            _ => throw new InvalidOperationException($"The '{this._recordType.Name}' type has multiple vector properties, please specify your chosen property via options.")
        };
    }

    /// <summary>
    /// Get the text data property, that has full text search indexing enabled, with the provided name if a name is provided, and fall back
    /// to a text data property in the schema if not. If no name is provided and there is more than one text data property with
    /// full text search indexing enabled, an exception will be thrown.
    /// </summary>
    /// <param name="expression">The full text search property selector.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided property name is not a valid text data property name.</exception>
    public VectorStoreRecordDataPropertyModel GetFullTextDataPropertyOrSingle<TRecord>(Expression<Func<TRecord, object?>>? expression)
    {
        if (expression is not null)
        {
            var property = this.GetMatchingProperty<TRecord, VectorStoreRecordDataPropertyModel>(expression, data: true);

            return property.IsFullTextSearchable
                ? property
                : throw new InvalidOperationException($"The property '{property.ModelName}' on '{this._recordType.Name}' must have full text search enabled.");
        }

        if (this._singleFullTextSearchProperty is null)
        {
            // If text data property name is not provided, check if a single full text searchable text property exists or throw otherwise.
            var fullTextStringProperties = this.DataProperties
                .Where(l => l.Type == typeof(string) && l.IsFullTextSearchable)
                .ToList();

            // If text data property name is not provided, check if a single full text searchable text property exists or throw otherwise.
            this._singleFullTextSearchProperty = fullTextStringProperties switch
            {
                [var singleProperty] => singleProperty,
                { Count: 0 } => throw new InvalidOperationException($"The '{this._recordType.Name}' type does not have any text data properties that have full text search enabled."),
                _ => throw new InvalidOperationException($"The '{this._recordType.Name}' type has multiple text data properties that have full text search enabled, please specify your chosen property via options.")
            };
        }

        return this._singleFullTextSearchProperty;
    }

    /// <summary>
    /// Get the data or key property selected by provided expression.
    /// </summary>
    /// <param name="expression">The property selector.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided property name is not a valid data or key property name.</exception>
    public VectorStoreRecordPropertyModel GetDataOrKeyProperty<TRecord>(Expression<Func<TRecord, object?>> expression)
        => this.GetMatchingProperty<TRecord, VectorStoreRecordPropertyModel>(expression, data: true);

    private TProperty GetMatchingProperty<TRecord, TProperty>(Expression<Func<TRecord, object?>> expression, bool data)
        where TProperty : VectorStoreRecordPropertyModel
    {
        string expectedGenericModelPropertyName = data
            ? nameof(VectorStoreGenericDataModel<object>.Data)
            : nameof(VectorStoreGenericDataModel<object>.Vectors);

        MemberExpression? member = expression.Body as MemberExpression;
        // (TRecord r) => r.PropertyName is translated into
        // (TRecord r) => (object)r.PropertyName for properties that return struct like ReadOnlyMemory<float>.
        if (member is null && expression.Body is UnaryExpression unary
            && unary.Operand.NodeType == ExpressionType.MemberAccess)
        {
            member = unary.Operand as MemberExpression;
        }

        if (member is { Member: PropertyInfo clrProperty }
            && expression.Parameters.Count == 1
            && member.Expression == expression.Parameters[0])
        {
            foreach (var property in this.Properties)
            {
                if (property.PropertyInfo == clrProperty)
                {
                    // TODO: Property error checking if the wrong property type is selected.
                    return (TProperty)property;
                }
            }

            throw new InvalidOperationException($"The property {clrProperty.Name} of {typeof(TRecord).FullName} is not a {(data ? "Data" : "Vector")} property.");
        }
        // (VectorStoreGenericDataModel r) => r.Vectors["PropertyName"]
        else if (expression.Body is MethodCallExpression methodCall
            // It's a Func<VectorStoreGenericDataModel<TKey>, object>
            && expression.Type.IsGenericType
            && expression.Type.GenericTypeArguments.Length == 2
            && expression.Type.GenericTypeArguments[0].IsGenericType
            && expression.Type.GenericTypeArguments[0].GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>)
            // It's accessing VectorStoreGenericDataModel.Vectors (or Data)
            && methodCall.Object is MemberExpression memberAccess
            && memberAccess.Member.Name == expectedGenericModelPropertyName
            // and has a single argument
            && methodCall.Arguments.Count == 1)
        {
            string name = methodCall.Arguments[0] switch
            {
                ConstantExpression constant when constant.Value is string text => text,
                MemberExpression field when TryGetCapturedValue(field, out object? capturedValue) && capturedValue is string text => text,
                _ => throw new InvalidOperationException($"The value of the provided {(data ? "Additional" : "Vector")}Property option is not a valid expression.")
            };

            // TODO: Property error checking if the wrong property type is selected.
            return (TProperty)(this.Properties.FirstOrDefault(p => p.ModelName == name)
                ?? throw new InvalidOperationException($"The {typeof(TRecord).FullName} type does not have a vector property named '{name}'."));
        }

        throw new InvalidOperationException($"The value of the provided {(data ? "Additional" : "Vector")}Property option is not a valid expression.");

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
