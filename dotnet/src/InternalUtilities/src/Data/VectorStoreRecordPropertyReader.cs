// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Contains helpers for reading vector store model properties and their attributes.
/// </summary>
[ExcludeFromCodeCoverage]
#pragma warning disable CA1812 // Used in some projects but not all, so need to suppress to avoid warnings in those it's not used in.
internal sealed class VectorStoreRecordPropertyReader
#pragma warning restore CA1812
{
    /// <summary>The <see cref="Type"/> of the data model.</summary>
    [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties | DynamicallyAccessedMemberTypes.PublicConstructors)]
    private readonly Type _dataModelType;

    /// <summary>A definition of the current storage model.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>Options for configuring the behavior of this class.</summary>
    private readonly VectorStoreRecordPropertyReaderOptions _options;

    /// <summary>The key properties from the definition.</summary>
    private readonly List<VectorStoreRecordKeyProperty> _keyProperties;

    /// <summary>The data properties from the definition.</summary>
    private readonly List<VectorStoreRecordDataProperty> _dataProperties;

    /// <summary>The vector properties from the definition.</summary>
    private readonly List<VectorStoreRecordVectorProperty> _vectorProperties;

    /// <summary>The <see cref="ConstructorInfo"/> of the parameterless constructor from the data model if one exists.</summary>
    private readonly Lazy<ConstructorInfo> _parameterlessConstructorInfo;

    /// <summary>The key <see cref="PropertyInfo"/> objects from the data model.</summary>
    private List<PropertyInfo>? _keyPropertiesInfo;

    /// <summary>The data <see cref="PropertyInfo"/> objects from the data model.</summary>
    private List<PropertyInfo>? _dataPropertiesInfo;

    /// <summary>The vector <see cref="PropertyInfo"/> objects from the data model.</summary>
    private List<PropertyInfo>? _vectorPropertiesInfo;

    /// <summary>A lazy initialized map of data model property names to the names under which they are stored in the data store.</summary>
    private readonly Lazy<Dictionary<string, string>> _storagePropertyNamesMap;

    /// <summary>A lazy initialized list of storage names of key properties.</summary>
    private readonly Lazy<List<string>> _keyPropertyStoragePropertyNames;

    /// <summary>A lazy initialized list of storage names of data properties.</summary>
    private readonly Lazy<List<string>> _dataPropertyStoragePropertyNames;

    /// <summary>A lazy initialized list of storage names of vector properties.</summary>
    private readonly Lazy<List<string>> _vectorPropertyStoragePropertyNames;

    /// <summary>A lazy initialized map of data model property names to the names they will have if serialized to JSON.</summary>
    private readonly Lazy<Dictionary<string, string>> _jsonPropertyNamesMap;

    /// <summary>A lazy initialized list of json names of key properties.</summary>
    private readonly Lazy<List<string>> _keyPropertyJsonNames;

    /// <summary>A lazy initialized list of json names of data properties.</summary>
    private readonly Lazy<List<string>> _dataPropertyJsonNames;

    /// <summary>A lazy initialized list of json names of vector properties.</summary>
    private readonly Lazy<List<string>> _vectorPropertyJsonNames;

    public VectorStoreRecordPropertyReader(
        [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties | DynamicallyAccessedMemberTypes.PublicConstructors)] Type dataModelType,
        VectorStoreRecordDefinition? vectorStoreRecordDefinition,
        VectorStoreRecordPropertyReaderOptions? options)
    {
        this._dataModelType = dataModelType;
        this._options = options ?? new VectorStoreRecordPropertyReaderOptions();

        // If a definition is provided, use it. Otherwise, create one from the type.
        if (vectorStoreRecordDefinition is not null)
        {
            // Here we received a definition, which gives us all of the information we need.
            // Some mappers though need to set properties on the data model using reflection
            // so we may still need to find the PropertyInfo objects on the data model later if required.
            this._vectorStoreRecordDefinition = vectorStoreRecordDefinition;
        }
        else
        {
            // Here we didn't receive a definition, so we need to derive the information from
            // the data model. Since we may need the PropertyInfo objects later to read or write
            // property values on the data model, we save them for later in case we need them.
            var propertiesInfo = FindPropertiesInfo(dataModelType);
            this._vectorStoreRecordDefinition = CreateVectorStoreRecordDefinitionFromType(propertiesInfo);

            this._keyPropertiesInfo = propertiesInfo.KeyProperties;
            this._dataPropertiesInfo = propertiesInfo.DataProperties;
            this._vectorPropertiesInfo = propertiesInfo.VectorProperties;
        }

        // Verify the definition to make sure it does not have too many or too few of each property type.
        (this._keyProperties, this._dataProperties, this._vectorProperties) = SplitDefinitionAndVerify(
            dataModelType.Name,
            this._vectorStoreRecordDefinition,
            this._options.SupportsMultipleKeys,
            this._options.SupportsMultipleVectors,
            this._options.RequiresAtLeastOneVector);

        // Setup lazy initializers.
        this._storagePropertyNamesMap = new Lazy<Dictionary<string, string>>(() =>
        {
            return BuildPropertyNameToStorageNameMap((this._keyProperties, this._dataProperties, this._vectorProperties));
        });

        this._parameterlessConstructorInfo = new Lazy<ConstructorInfo>(() =>
        {
            var constructor = dataModelType.GetConstructor(Type.EmptyTypes);
            if (constructor == null)
            {
                throw new ArgumentException($"Type {dataModelType.FullName} must have a parameterless constructor.");
            }

            return constructor;
        });

        this._keyPropertyStoragePropertyNames = new Lazy<List<string>>(() =>
        {
            var storagePropertyNames = this._storagePropertyNamesMap.Value;
            return this._keyProperties.Select(x => storagePropertyNames[x.DataModelPropertyName]).ToList();
        });

        this._dataPropertyStoragePropertyNames = new Lazy<List<string>>(() =>
        {
            var storagePropertyNames = this._storagePropertyNamesMap.Value;
            return this._dataProperties.Select(x => storagePropertyNames[x.DataModelPropertyName]).ToList();
        });

        this._vectorPropertyStoragePropertyNames = new Lazy<List<string>>(() =>
        {
            var storagePropertyNames = this._storagePropertyNamesMap.Value;
            return this._vectorProperties.Select(x => storagePropertyNames[x.DataModelPropertyName]).ToList();
        });

        this._jsonPropertyNamesMap = new Lazy<Dictionary<string, string>>(() =>
        {
            return BuildPropertyNameToJsonPropertyNameMap(
                (this._keyProperties, this._dataProperties, this._vectorProperties),
                dataModelType,
                this._options?.JsonSerializerOptions);
        });

        this._keyPropertyJsonNames = new Lazy<List<string>>(() =>
        {
            var jsonPropertyNamesMap = this._jsonPropertyNamesMap.Value;
            return this._keyProperties.Select(x => jsonPropertyNamesMap[x.DataModelPropertyName]).ToList();
        });

        this._dataPropertyJsonNames = new Lazy<List<string>>(() =>
        {
            var jsonPropertyNamesMap = this._jsonPropertyNamesMap.Value;
            return this._dataProperties.Select(x => jsonPropertyNamesMap[x.DataModelPropertyName]).ToList();
        });

        this._vectorPropertyJsonNames = new Lazy<List<string>>(() =>
        {
            var jsonPropertyNamesMap = this._jsonPropertyNamesMap.Value;
            return this._vectorProperties.Select(x => jsonPropertyNamesMap[x.DataModelPropertyName]).ToList();
        });
    }

    /// <summary>Gets the record definition of the current storage model.</summary>
    public VectorStoreRecordDefinition RecordDefinition => this._vectorStoreRecordDefinition;

    /// <summary>Gets the list of properties from the record definition.</summary>
    public IReadOnlyList<VectorStoreRecordProperty> Properties => this._vectorStoreRecordDefinition.Properties;

    /// <summary>Gets the first <see cref="VectorStoreRecordKeyProperty"/> object from the record definition that was provided or that was generated from the data model.</summary>
    public VectorStoreRecordKeyProperty KeyProperty => this._keyProperties[0];

    /// <summary>Gets all <see cref="VectorStoreRecordKeyProperty"/> objects from the record definition that was provided or that was generated from the data model.</summary>
    public IReadOnlyList<VectorStoreRecordKeyProperty> KeyProperties => this._keyProperties;

    /// <summary>Gets all <see cref="VectorStoreRecordDataProperty"/> objects from the record definition that was provided or that was generated from the data model.</summary>
    public IReadOnlyList<VectorStoreRecordDataProperty> DataProperties => this._dataProperties;

    /// <summary>Gets the first <see cref="VectorStoreRecordVectorProperty"/> objects from the record definition that was provided or that was generated from the data model.</summary>
    public VectorStoreRecordVectorProperty? VectorProperty => this._vectorProperties.Count > 0 ? this._vectorProperties[0] : null;

    /// <summary>Gets all <see cref="VectorStoreRecordVectorProperty"/> objects from the record definition that was provided or that was generated from the data model.</summary>
    public IReadOnlyList<VectorStoreRecordVectorProperty> VectorProperties => this._vectorProperties;

    /// <summary>Gets the parameterless constructor if one exists, throws otherwise.</summary>
    public ConstructorInfo ParameterLessConstructorInfo => this._parameterlessConstructorInfo.Value;

    /// <summary>Gets the first key property info object.</summary>
    public PropertyInfo KeyPropertyInfo
    {
        get
        {
            this.LoadPropertyInfoIfNeeded();
            return this._keyPropertiesInfo![0];
        }
    }

    /// <summary>Gets the key property info objects.</summary>
    public IReadOnlyList<PropertyInfo> KeyPropertiesInfo
    {
        get
        {
            this.LoadPropertyInfoIfNeeded();
            return this._keyPropertiesInfo!;
        }
    }

    /// <summary>Gets the data property info objects.</summary>
    public IReadOnlyList<PropertyInfo> DataPropertiesInfo
    {
        get
        {
            this.LoadPropertyInfoIfNeeded();
            return this._dataPropertiesInfo!;
        }
    }

    /// <summary>Gets the vector property info objects.</summary>
    public IReadOnlyList<PropertyInfo> VectorPropertiesInfo
    {
        get
        {
            this.LoadPropertyInfoIfNeeded();
            return this._vectorPropertiesInfo!;
        }
    }

    /// <summary>Gets the name of the first vector property in the definition or null if there are no vectors.</summary>
    public string? FirstVectorPropertyName => this._vectorProperties.FirstOrDefault()?.DataModelPropertyName;

    /// <summary>Gets the first vector PropertyInfo object in the data model or null if there are no vectors.</summary>
    public PropertyInfo? FirstVectorPropertyInfo => this.VectorPropertiesInfo.Count > 0 ? this.VectorPropertiesInfo[0] : null;

    /// <summary>Gets the property name of the first key property in the definition.</summary>
    public string KeyPropertyName => this._keyProperties[0].DataModelPropertyName;

    /// <summary>Gets the storage name of the first key property in the definition.</summary>
    public string KeyPropertyStoragePropertyName => this._keyPropertyStoragePropertyNames.Value[0];

    /// <summary>Gets the storage names of all the properties in the definition.</summary>
    public IReadOnlyDictionary<string, string> StoragePropertyNamesMap => this._storagePropertyNamesMap.Value;

    /// <summary>Gets the storage names of the key properties in the definition.</summary>
    public IReadOnlyList<string> KeyPropertyStoragePropertyNames => this._keyPropertyStoragePropertyNames.Value;

    /// <summary>Gets the storage names of the data properties in the definition.</summary>
    public IReadOnlyList<string> DataPropertyStoragePropertyNames => this._dataPropertyStoragePropertyNames.Value;

    /// <summary>Gets the storage name of the first vector property in the definition or null if there are no vectors.</summary>
    public string? FirstVectorPropertyStoragePropertyName => this.FirstVectorPropertyName == null ? null : this.StoragePropertyNamesMap[this.FirstVectorPropertyName];

    /// <summary>Gets the storage names of the vector properties in the definition.</summary>
    public IReadOnlyList<string> VectorPropertyStoragePropertyNames => this._vectorPropertyStoragePropertyNames.Value;

    /// <summary>Gets the json name of the first key property in the definition.</summary>
    public string KeyPropertyJsonName => this.KeyPropertyJsonNames[0];

    /// <summary>Gets the json names of the key properties in the definition.</summary>
    public IReadOnlyList<string> KeyPropertyJsonNames => this._keyPropertyJsonNames.Value;

    /// <summary>Gets the json names of the data properties in the definition.</summary>
    public IReadOnlyList<string> DataPropertyJsonNames => this._dataPropertyJsonNames.Value;

    /// <summary>Gets the json name of the first vector property in the definition or null if there are no vectors.</summary>
    public string? FirstVectorPropertyJsonName => this.FirstVectorPropertyName == null ? null : this.JsonPropertyNamesMap[this.FirstVectorPropertyName];

    /// <summary>Gets the json names of the vector properties in the definition.</summary>
    public IReadOnlyList<string> VectorPropertyJsonNames => this._vectorPropertyJsonNames.Value;

    /// <summary>A map of data model property names to the names they will have if serialized to JSON.</summary>
    public IReadOnlyDictionary<string, string> JsonPropertyNamesMap => this._jsonPropertyNamesMap.Value;

    /// <summary>Verify that the data model has a parameterless constructor.</summary>
    public void VerifyHasParameterlessConstructor()
    {
        var constructorInfo = this._parameterlessConstructorInfo.Value;
    }

    /// <summary>Verify that the types of the key properties fall within the provided set.</summary>
    /// <param name="supportedTypes">The list of supported types.</param>
    public void VerifyKeyProperties(HashSet<Type> supportedTypes)
    {
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(this._keyProperties, supportedTypes, "Key");
    }

    /// <summary>Verify that the types of the data properties fall within the provided set.</summary>
    /// <param name="supportedTypes">The list of supported types.</param>
    /// <param name="supportEnumerable">A value indicating whether enumerable types are supported where the element type is one of the supported types.</param>
    public void VerifyDataProperties(HashSet<Type> supportedTypes, bool supportEnumerable)
    {
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(this._dataProperties, supportedTypes, "Data", supportEnumerable);
    }

    /// <summary>Verify that the types of the data properties fall within the provided set.</summary>
    /// <param name="supportedTypes">The list of supported types.</param>
    /// <param name="supportedEnumerableElementTypes">A value indicating whether enumerable types are supported where the element type is one of the supported types.</param>
    public void VerifyDataProperties(HashSet<Type> supportedTypes, HashSet<Type> supportedEnumerableElementTypes)
    {
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(this._dataProperties, supportedTypes, supportedEnumerableElementTypes, "Data");
    }

    /// <summary>Verify that the types of the vector properties fall within the provided set.</summary>
    /// <param name="supportedTypes">The list of supported types.</param>
    public void VerifyVectorProperties(HashSet<Type> supportedTypes)
    {
        VectorStoreRecordPropertyVerification.VerifyPropertyTypes(this._vectorProperties, supportedTypes, "Vector");
    }

    /// <summary>
    /// Get the storage property name for the given data model property name.
    /// </summary>
    /// <param name="dataModelPropertyName">The data model property name for which to get the storage property name.</param>
    /// <returns>The storage property name.</returns>
    public string GetStoragePropertyName(string dataModelPropertyName)
    {
        return this._storagePropertyNamesMap.Value[dataModelPropertyName];
    }

    /// <summary>
    /// Get the name under which a property will be stored if serialized to JSON
    /// </summary>
    /// <param name="dataModelPropertyName">The data model property name for which to get the JSON name.</param>
    /// <returns>The JSON name.</returns>
    public string GetJsonPropertyName(string dataModelPropertyName)
    {
        return this._jsonPropertyNamesMap.Value[dataModelPropertyName];
    }

    /// <summary>
    /// Get the vector property with the provided name if a name is provided, and fall back
    /// to a vector property in the schema if not. If no name is provided and there is more
    /// than one vector property, an exception will be thrown.
    /// </summary>
    /// <param name="searchOptions">The search options.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided property name is not a valid vector property name.</exception>
    public VectorStoreRecordVectorProperty GetVectorPropertyOrSingle<TRecord>(VectorSearchOptions<TRecord>? searchOptions)
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
                return this.VectorProperties.FirstOrDefault(l => l.DataModelPropertyName.Equals(vectorPropertyName, StringComparison.Ordinal))
                    ?? throw new InvalidOperationException($"The {this._dataModelType.FullName} type does not have a vector property named '{vectorPropertyName}'.");
            }
            else if (searchOptions.VectorProperty is Expression<Func<TRecord, object?>> expression)
            {
                // VectorPropertiesInfo is not available for VectorStoreGenericDataModel.
                IReadOnlyList<PropertyInfo> infos = typeof(TRecord).IsGenericType && typeof(TRecord).GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>)
                    ? [] : this.VectorPropertiesInfo;

                return GetMatchingProperty<TRecord, VectorStoreRecordVectorProperty>(expression, infos, this.VectorProperties);
            }
        }

        // If vector property name is not provided, check if there is a single vector property, or throw if there are no vectors or more than one.
        if (this.VectorProperty is null)
        {
            throw new InvalidOperationException($"The {this._dataModelType.FullName} type does not have any vector properties.");
        }

        if (this.VectorProperties.Count > 1)
        {
            throw new InvalidOperationException($"The {this._dataModelType.FullName} type has multiple vector properties, please specify your chosen property via options.");
        }

        return this.VectorProperty;
    }

    /// <summary>
    /// Get the text data property, that has full text search indexing enabled, with the provided name if a name is provided, and fall back
    /// to a text data property in the schema if not. If no name is provided and there is more than one text data property with
    /// full text search indexing enabled, an exception will be thrown.
    /// </summary>
    /// <param name="expression">The full text search property selector.</param>
    /// <exception cref="InvalidOperationException">Thrown if the provided property name is not a valid text data property name.</exception>
    public VectorStoreRecordDataProperty GetFullTextDataPropertyOrSingle<TRecord>(Expression<Func<TRecord, object?>>? expression)
    {
        if (expression is not null)
        {
            // DataPropertiesInfo is not available for VectorStoreGenericDataModel.
            IReadOnlyList<PropertyInfo> infos = typeof(TRecord).IsGenericType && typeof(TRecord).GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>)
                ? [] : this.DataPropertiesInfo;

            var dataProperty = GetMatchingProperty<TRecord, VectorStoreRecordDataProperty>(expression, this.DataPropertiesInfo, this.DataProperties);
            return dataProperty.IsFullTextSearchable
                ? dataProperty
                : throw new InvalidOperationException($"The text data property named '{dataProperty.DataModelPropertyName}' on the {this._dataModelType.FullName} type must have full text search enabled.");
        }

        // If text data property name is not provided, check if a single full text searchable text property exists or throw otherwise.
        var fullTextStringProperties = this.DataProperties
            .Where(l => l.PropertyType == typeof(string) && l.IsFullTextSearchable)
            .ToList();

        if (fullTextStringProperties.Count == 0)
        {
            throw new InvalidOperationException($"The {this._dataModelType.FullName} type does not have any text data properties that have full text search enabled.");
        }

        if (fullTextStringProperties.Count > 1)
        {
            throw new InvalidOperationException($"The {this._dataModelType.FullName} type has multiple text data properties that have full text search enabled, please specify your chosen property via options.");
        }

        return fullTextStringProperties[0];
    }

    private static TProperty GetMatchingProperty<TRecord, TProperty>(Expression<Func<TRecord, object?>> expression,
        IReadOnlyList<PropertyInfo> propertyInfos, IReadOnlyList<TProperty> properties)
        where TProperty : VectorStoreRecordProperty
    {
        bool data = typeof(TProperty) == typeof(VectorStoreRecordDataProperty);
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

        if (member is not null
            && expression.Parameters.Count == 1
            && member.Expression == expression.Parameters[0]
            && member.Member is PropertyInfo property)
        {
            for (int i = 0; i < propertyInfos.Count; i++)
            {
                if (propertyInfos[i] == property)
                {
                    return properties[i];
                }
            }

            throw new InvalidOperationException($"The property {property.Name} of {typeof(TRecord).FullName} is not a {(data ? "Data" : "Vector")} property.");
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

            return properties.FirstOrDefault(l => l.DataModelPropertyName.Equals(name, StringComparison.Ordinal))
                ?? throw new InvalidOperationException($"The {typeof(TRecord).FullName} type does not have a vector property named '{name}'.");
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

    /// <summary>
    /// Check if we have previously loaded the <see cref="PropertyInfo"/> objects from the data model and if not, load them.
    /// </summary>
    private void LoadPropertyInfoIfNeeded()
    {
        if (this._keyPropertiesInfo != null)
        {
            return;
        }

        // If we previously built the definition from the data model, the PropertyInfo objects
        // from the data model would already be saved. If we didn't though, there could be a mismatch
        // between what is defined in the definition and what is in the data model. Therefore, this
        // method will throw if any property in the definition is not on the data model.
        var propertiesInfo = FindPropertiesInfo(this._dataModelType, this._vectorStoreRecordDefinition);

        this._keyPropertiesInfo = propertiesInfo.KeyProperties;
        this._dataPropertiesInfo = propertiesInfo.DataProperties;
        this._vectorPropertiesInfo = propertiesInfo.VectorProperties;
    }

    /// <summary>
    /// Split the given <paramref name="definition"/> into key, data and vector properties and verify that we have the expected numbers of each type.
    /// </summary>
    /// <param name="typeName">The name of the type that the definition relates to.</param>
    /// <param name="definition">The <see cref="VectorStoreRecordDefinition"/> to split.</param>
    /// <param name="supportsMultipleKeys">A value indicating whether multiple key properties are supported.</param>
    /// <param name="supportsMultipleVectors">A value indicating whether multiple vectors are supported.</param>
    /// <param name="requiresAtLeastOneVector">A value indicating whether we need at least one vector.</param>
    /// <returns>The properties on the <see cref="VectorStoreRecordDefinition"/> split into key, data and vector groupings.</returns>
    /// <exception cref="ArgumentException">Thrown if there are any validation failures with the provided <paramref name="definition"/>.</exception>
    private static (List<VectorStoreRecordKeyProperty> KeyProperties, List<VectorStoreRecordDataProperty> DataProperties, List<VectorStoreRecordVectorProperty> VectorProperties) SplitDefinitionAndVerify(
        string typeName,
        VectorStoreRecordDefinition definition,
        bool supportsMultipleKeys,
        bool supportsMultipleVectors,
        bool requiresAtLeastOneVector)
    {
        var keyProperties = definition.Properties.OfType<VectorStoreRecordKeyProperty>().ToList();
        var dataProperties = definition.Properties.OfType<VectorStoreRecordDataProperty>().ToList();
        var vectorProperties = definition.Properties.OfType<VectorStoreRecordVectorProperty>().ToList();

        if (keyProperties.Count > 1 && !supportsMultipleKeys)
        {
            throw new ArgumentException($"Multiple key properties found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)}.");
        }

        if (keyProperties.Count == 0)
        {
            throw new ArgumentException($"No key property found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)}.");
        }

        if (requiresAtLeastOneVector && vectorProperties.Count == 0)
        {
            throw new ArgumentException($"No vector property found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)} while at least one is required.");
        }

        if (!supportsMultipleVectors && vectorProperties.Count > 1)
        {
            throw new ArgumentException($"Multiple vector properties found on type {typeName} or the provided {nameof(VectorStoreRecordDefinition)} while only one is supported.");
        }

        return (keyProperties, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Find the properties with <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/> attributes
    /// and verify that they exist and that we have the expected numbers of each type.
    /// Return those properties in separate categories.
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <returns>The categorized properties.</returns>
    private static (List<PropertyInfo> KeyProperties, List<PropertyInfo> DataProperties, List<PropertyInfo> VectorProperties) FindPropertiesInfo([DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type type)
    {
        List<PropertyInfo> keyProperties = new();
        List<PropertyInfo> dataProperties = new();
        List<PropertyInfo> vectorProperties = new();

        foreach (var property in type.GetProperties())
        {
            // Get Key property.
            if (property.GetCustomAttribute<VectorStoreRecordKeyAttribute>() is not null)
            {
                keyProperties.Add(property);
            }

            // Get data properties.
            if (property.GetCustomAttribute<VectorStoreRecordDataAttribute>() is not null)
            {
                dataProperties.Add(property);
            }

            // Get Vector properties.
            if (property.GetCustomAttribute<VectorStoreRecordVectorAttribute>() is not null)
            {
                vectorProperties.Add(property);
            }
        }

        return (keyProperties, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Find the properties listed in the <paramref name="vectorStoreRecordDefinition"/> on the <paramref name="type"/> and verify
    /// that they exist.
    /// Return those properties in separate categories.
    /// </summary>
    /// <param name="type">The data model to find the properties on.</param>
    /// <param name="vectorStoreRecordDefinition">The property configuration.</param>
    /// <returns>The categorized properties.</returns>
    public static (List<PropertyInfo> KeyProperties, List<PropertyInfo> DataProperties, List<PropertyInfo> VectorProperties) FindPropertiesInfo([DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type type, VectorStoreRecordDefinition vectorStoreRecordDefinition)
    {
        List<PropertyInfo> keyProperties = new();
        List<PropertyInfo> dataProperties = new();
        List<PropertyInfo> vectorProperties = new();

        foreach (VectorStoreRecordProperty property in vectorStoreRecordDefinition.Properties)
        {
            // Key.
            if (property is VectorStoreRecordKeyProperty keyPropertyInfo)
            {
                var keyProperty = type.GetProperty(keyPropertyInfo.DataModelPropertyName);
                if (keyProperty == null)
                {
                    throw new ArgumentException($"Key property '{keyPropertyInfo.DataModelPropertyName}' not found on type {type.FullName}.");
                }

                keyProperties.Add(keyProperty);
            }
            // Data.
            else if (property is VectorStoreRecordDataProperty dataPropertyInfo)
            {
                var dataProperty = type.GetProperty(dataPropertyInfo.DataModelPropertyName);
                if (dataProperty == null)
                {
                    throw new ArgumentException($"Data property '{dataPropertyInfo.DataModelPropertyName}' not found on type {type.FullName}.");
                }

                dataProperties.Add(dataProperty);
            }
            // Vector.
            else if (property is VectorStoreRecordVectorProperty vectorPropertyInfo)
            {
                var vectorProperty = type.GetProperty(vectorPropertyInfo.DataModelPropertyName);
                if (vectorProperty == null)
                {
                    throw new ArgumentException($"Vector property '{vectorPropertyInfo.DataModelPropertyName}' not found on type {type.FullName}.");
                }

                vectorProperties.Add(vectorProperty);
            }
            else
            {
                throw new ArgumentException($"Unknown property type '{property.GetType().FullName}' in vector store record definition.");
            }
        }

        return (keyProperties, dataProperties, vectorProperties);
    }

    /// <summary>
    /// Create a <see cref="VectorStoreRecordDefinition"/> by reading the attributes on the provided <see cref="PropertyInfo"/> objects.
    /// </summary>
    /// <param name="propertiesInfo"><see cref="PropertyInfo"/> objects to build a <see cref="VectorStoreRecordDefinition"/> from.</param>
    /// <returns>The <see cref="VectorStoreRecordDefinition"/> based on the given <see cref="PropertyInfo"/> objects.</returns>
    private static VectorStoreRecordDefinition CreateVectorStoreRecordDefinitionFromType((List<PropertyInfo> KeyProperties, List<PropertyInfo> DataProperties, List<PropertyInfo> VectorProperties) propertiesInfo)
    {
        var definitionProperties = new List<VectorStoreRecordProperty>();

        // Key properties.
        foreach (var keyProperty in propertiesInfo.KeyProperties)
        {
            var keyAttribute = keyProperty.GetCustomAttribute<VectorStoreRecordKeyAttribute>();
            if (keyAttribute is not null)
            {
                definitionProperties.Add(new VectorStoreRecordKeyProperty(keyProperty.Name, keyProperty.PropertyType)
                {
                    StoragePropertyName = keyAttribute.StoragePropertyName
                });
            }
        }

        // Data properties.
        foreach (var dataProperty in propertiesInfo.DataProperties)
        {
            var dataAttribute = dataProperty.GetCustomAttribute<VectorStoreRecordDataAttribute>();
            if (dataAttribute is not null)
            {
                definitionProperties.Add(new VectorStoreRecordDataProperty(dataProperty.Name, dataProperty.PropertyType)
                {
                    IsFilterable = dataAttribute.IsFilterable,
                    IsFullTextSearchable = dataAttribute.IsFullTextSearchable,
                    StoragePropertyName = dataAttribute.StoragePropertyName
                });
            }
        }

        // Vector properties.
        foreach (var vectorProperty in propertiesInfo.VectorProperties)
        {
            var vectorAttribute = vectorProperty.GetCustomAttribute<VectorStoreRecordVectorAttribute>();
            if (vectorAttribute is not null)
            {
                definitionProperties.Add(new VectorStoreRecordVectorProperty(vectorProperty.Name, vectorProperty.PropertyType)
                {
                    Dimensions = vectorAttribute.Dimensions,
                    IndexKind = vectorAttribute.IndexKind,
                    DistanceFunction = vectorAttribute.DistanceFunction,
                    StoragePropertyName = vectorAttribute.StoragePropertyName
                });
            }
        }

        return new VectorStoreRecordDefinition { Properties = definitionProperties };
    }

    /// <summary>
    /// Build a map of property names to the names under which they should be saved in storage, for the given properties.
    /// </summary>
    /// <param name="properties">The properties to build the map for.</param>
    /// <returns>The map from property names to the names under which they should be saved in storage.</returns>
    private static Dictionary<string, string> BuildPropertyNameToStorageNameMap((List<VectorStoreRecordKeyProperty> keyProperties, List<VectorStoreRecordDataProperty> dataProperties, List<VectorStoreRecordVectorProperty> vectorProperties) properties)
    {
        var storagePropertyNameMap = new Dictionary<string, string>();

        foreach (var keyProperty in properties.keyProperties)
        {
            storagePropertyNameMap.Add(keyProperty.DataModelPropertyName, keyProperty.StoragePropertyName ?? keyProperty.DataModelPropertyName);
        }

        foreach (var dataProperty in properties.dataProperties)
        {
            storagePropertyNameMap.Add(dataProperty.DataModelPropertyName, dataProperty.StoragePropertyName ?? dataProperty.DataModelPropertyName);
        }

        foreach (var vectorProperty in properties.vectorProperties)
        {
            storagePropertyNameMap.Add(vectorProperty.DataModelPropertyName, vectorProperty.StoragePropertyName ?? vectorProperty.DataModelPropertyName);
        }

        return storagePropertyNameMap;
    }

    /// <summary>
    /// Build a map of property names to the names that they would have if serialized to JSON.
    /// </summary>
    /// <param name="properties">The properties to build the map for.</param>
    /// <param name="dataModel">The data model type that the property belongs to.</param>
    /// <param name="options">The options used for JSON serialization.</param>
    /// <returns>The map from property names to the names that they would have if serialized to JSON.</returns>
    private static Dictionary<string, string> BuildPropertyNameToJsonPropertyNameMap(
        (List<VectorStoreRecordKeyProperty> keyProperties, List<VectorStoreRecordDataProperty> dataProperties, List<VectorStoreRecordVectorProperty> vectorProperties) properties,
        [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type dataModel,
        JsonSerializerOptions? options)
    {
        var jsonPropertyNameMap = new Dictionary<string, string>();

        foreach (var keyProperty in properties.keyProperties)
        {
            jsonPropertyNameMap.Add(keyProperty.DataModelPropertyName, GetJsonPropertyName(keyProperty, dataModel, options));
        }

        foreach (var dataProperty in properties.dataProperties)
        {
            jsonPropertyNameMap.Add(dataProperty.DataModelPropertyName, GetJsonPropertyName(dataProperty, dataModel, options));
        }

        foreach (var vectorProperty in properties.vectorProperties)
        {
            jsonPropertyNameMap.Add(vectorProperty.DataModelPropertyName, GetJsonPropertyName(vectorProperty, dataModel, options));
        }

        return jsonPropertyNameMap;
    }

    /// <summary>
    /// Get the JSON property name of a property by using the <see cref="JsonPropertyNameAttribute"/> if available, otherwise
    /// using the <see cref="JsonNamingPolicy"/> if available, otherwise falling back to the property name.
    /// The provided <paramref name="dataModel"/> may not actually contain the property, e.g. when the user has a data model that
    /// doesn't resemble the stored data and where they are using a custom mapper.
    /// </summary>
    /// <param name="property">The property to retrieve a JSON name for.</param>
    /// <param name="dataModel">The data model type that the property belongs to.</param>
    /// <param name="options">The options used for JSON serialization.</param>
    /// <returns>The JSON property name.</returns>
    private static string GetJsonPropertyName(VectorStoreRecordProperty property, [DynamicallyAccessedMembers(DynamicallyAccessedMemberTypes.PublicProperties)] Type dataModel, JsonSerializerOptions? options)
    {
        var propertyInfo = dataModel.GetProperty(property.DataModelPropertyName);

        if (propertyInfo != null)
        {
            var jsonPropertyNameAttribute = propertyInfo.GetCustomAttribute<JsonPropertyNameAttribute>();
            if (jsonPropertyNameAttribute is not null)
            {
                return jsonPropertyNameAttribute.Name;
            }
        }

        if (options?.PropertyNamingPolicy is not null)
        {
            return options.PropertyNamingPolicy.ConvertName(property.DataModelPropertyName);
        }

        return property.DataModelPropertyName;
    }
}
