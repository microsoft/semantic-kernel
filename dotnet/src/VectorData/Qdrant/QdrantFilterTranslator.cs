// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using Google.Protobuf.Collections;
using Google.Protobuf.WellKnownTypes;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.Extensions.VectorData.ProviderServices.Filter;
using Qdrant.Client.Grpc;
using Expression = System.Linq.Expressions.Expression;
using Range = Qdrant.Client.Grpc.Range;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

// https://qdrant.tech/documentation/concepts/filtering
internal class QdrantFilterTranslator
{
    private CollectionModel _model = null!;
    private ParameterExpression _recordParameter = null!;

    internal Filter Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        this._model = model;

        Debug.Assert(lambdaExpression.Parameters.Count == 1);
        this._recordParameter = lambdaExpression.Parameters[0];

        var preprocessor = new FilterTranslationPreprocessor { SupportsParameterization = false };
        var preprocessedExpression = preprocessor.Preprocess(lambdaExpression.Body);

        return this.Translate(preprocessedExpression);
    }

    private Filter Translate(Expression? node)
        => node switch
        {
            BinaryExpression { NodeType: ExpressionType.Equal } equal => this.TranslateEqual(equal.Left, equal.Right),
            BinaryExpression { NodeType: ExpressionType.NotEqual } notEqual => this.TranslateEqual(notEqual.Left, notEqual.Right, negated: true),

            BinaryExpression
            {
                NodeType: ExpressionType.GreaterThan or ExpressionType.GreaterThanOrEqual or ExpressionType.LessThan or ExpressionType.LessThanOrEqual
            } comparison
                => this.TranslateComparison(comparison),

            BinaryExpression { NodeType: ExpressionType.AndAlso } andAlso => this.TranslateAndAlso(andAlso.Left, andAlso.Right),
            BinaryExpression { NodeType: ExpressionType.OrElse } orElse => this.TranslateOrElse(orElse.Left, orElse.Right),

            UnaryExpression { NodeType: ExpressionType.Not } not => this.TranslateNot(not.Operand),
            // Handle converting non-nullable to nullable; such nodes are found in e.g. r => r.Int == nullableInt
            UnaryExpression { NodeType: ExpressionType.Convert } convert when Nullable.GetUnderlyingType(convert.Type) == convert.Operand.Type
                => this.Translate(convert.Operand),

            // Special handling for bool constant as the filter expression (r => r.Bool)
            Expression when node.Type == typeof(bool) && this.TryBindProperty(node, out var property)
                => this.GenerateEqual(property.StorageName, value: true),
            // Handle true literal (r => true), which is useful for fetching all records
            ConstantExpression { Value: true } => new Filter(),

            MethodCallExpression methodCall => this.TranslateMethodCall(methodCall),

            _ => throw new NotSupportedException("Qdrant does not support the following NodeType in filters: " + node?.NodeType)
        };

    private Filter TranslateEqual(Expression left, Expression right, bool negated = false)
        => this.TryBindProperty(left, out var property) && right is ConstantExpression { Value: var rightConstant }
            ? this.GenerateEqual(property.StorageName, rightConstant, negated)
            : this.TryBindProperty(right, out property) && left is ConstantExpression { Value: var leftConstant }
                ? this.GenerateEqual(property.StorageName, leftConstant, negated)
                : throw new NotSupportedException("Invalid equality/comparison");

    private Filter GenerateEqual(string propertyStorageName, object? value, bool negated = false)
    {
        var condition = value is null
            ? new Condition { IsNull = new() { Key = propertyStorageName } }
            : new Condition
            {
                Field = new FieldCondition
                {
                    Key = propertyStorageName,
                    Match = value switch
                    {
                        string v => new Match { Keyword = v },
                        int v => new Match { Integer = v },
                        long v => new Match { Integer = v },
                        bool v => new Match { Boolean = v },
                        DateTimeOffset v => new Match { Keyword = v.ToString("o") },

                        _ => throw new NotSupportedException($"Unsupported filter value type '{value.GetType().Name}'.")
                    }
                }
            };

        var result = new Filter();

        if (negated)
        {
            result.MustNot.Add(condition);
        }
        else
        {
            result.Must.Add(condition);
        }

        return result;
    }

    private Filter TranslateComparison(BinaryExpression comparison)
    {
        return TryProcessComparison(comparison.Left, comparison.Right, out var result)
            ? result
            : TryProcessComparison(comparison.Right, comparison.Left, out result)
                ? result
                : throw new NotSupportedException("Comparison expression not supported by Qdrant");

        bool TryProcessComparison(Expression first, Expression second, [NotNullWhen(true)] out Filter? result)
        {
            if (this.TryBindProperty(first, out var property) && second is ConstantExpression { Value: var constantValue })
            {
                result = new Filter();
                result.Must.Add(new Condition
                {
                    Field = constantValue switch
                    {
                        double v => DoubleFieldCondition(v),
                        int v => DoubleFieldCondition(v),
                        long v => DoubleFieldCondition(v),

                        DateTimeOffset v => new FieldCondition
                        {
                            Key = property.StorageName,
                            DatetimeRange = new DatetimeRange
                            {
                                Gt = comparison.NodeType == ExpressionType.GreaterThan ? Timestamp.FromDateTimeOffset(v) : null,
                                Gte = comparison.NodeType == ExpressionType.GreaterThanOrEqual ? Timestamp.FromDateTimeOffset(v) : null,
                                Lt = comparison.NodeType == ExpressionType.LessThan ? Timestamp.FromDateTimeOffset(v) : null,
                                Lte = comparison.NodeType == ExpressionType.LessThanOrEqual ? Timestamp.FromDateTimeOffset(v) : null
                            }
                        },

                        _ => throw new NotSupportedException($"Can't perform comparison on type '{constantValue?.GetType().Name}'")
                    }
                });

                return true;

                FieldCondition DoubleFieldCondition(double d)
                    => new()
                    {
                        Key = property.StorageName,
                        Range = comparison.NodeType switch
                        {
                            ExpressionType.GreaterThan => new Range { Gt = d },
                            ExpressionType.GreaterThanOrEqual => new Range { Gte = d },
                            ExpressionType.LessThan => new Range { Lt = d },
                            ExpressionType.LessThanOrEqual => new Range { Lte = d },

                            _ => throw new InvalidOperationException("Unreachable")
                        }
                    };
            }

            result = null;
            return false;
        }
    }

    #region Logical operators

    private Filter TranslateAndAlso(Expression left, Expression right)
    {
        var leftFilter = this.Translate(left);
        var rightFilter = this.Translate(right);

        // As long as there are only AND conditions (Must or MustNot), we can simply combine both filters into a single flat one.
        // The moment there's a Should, things become a bit more complicated:
        // 1. If a side contains both a Should and a Must/MustNot, it must be pushed down.
        // 2. Otherwise, if the left's Should is empty, and the right side is only Should, we can just copy the right Should into the left's.
        // 3. Finally, if both sides have a Should, we push down the right side and put the result in the left's Must.
        if (leftFilter.Should.Count > 0 && (leftFilter.Must.Count > 0 || leftFilter.MustNot.Count > 0))
        {
            leftFilter = new Filter { Must = { new Condition { Filter = leftFilter } } };
        }

        if (rightFilter.Should.Count > 0 && (rightFilter.Must.Count > 0 || rightFilter.MustNot.Count > 0))
        {
            rightFilter = new Filter { Must = { new Condition { Filter = rightFilter } } };
        }

        if (rightFilter.Should.Count > 0)
        {
            if (leftFilter.Should.Count == 0)
            {
                leftFilter.Should.AddRange(rightFilter.Should);
            }
            else
            {
                rightFilter = new Filter { Must = { new Condition { Filter = rightFilter } } };
            }
        }

        leftFilter.Must.AddRange(rightFilter.Must);
        leftFilter.MustNot.AddRange(rightFilter.MustNot);

        return leftFilter;
    }

    private Filter TranslateOrElse(Expression left, Expression right)
    {
        var leftFilter = this.Translate(left);
        var rightFilter = this.Translate(right);

        var result = new Filter();
        result.Should.AddRange(GetShouldConditions(leftFilter));
        result.Should.AddRange(GetShouldConditions(rightFilter));
        return result;

        static RepeatedField<Condition> GetShouldConditions(Filter filter)
            => filter switch
            {
                // If the filter only contains Should conditions (string of ORs), those can be directly added to the result
                // (concatenated into the Should with whatever comes out of the other side)
                { Must.Count: 0, MustNot.Count: 0 } => filter.Should,

                // If the filter is just a single Must condition, it can also be directly added to the result.
                { Must.Count: 1, MustNot.Count: 0, Should.Count: 0 } => [filter.Must[0]],

                // For all other cases, we need to wrap the filter in a condition and return that, to preserve the logical structure.
                _ => [new Condition { Filter = filter }]
            };
    }

    private Filter TranslateNot(Expression expression)
    {
        // Special handling for !(a == b) and !(a != b)
        if (expression is BinaryExpression { NodeType: ExpressionType.Equal or ExpressionType.NotEqual } binary)
        {
            return this.TranslateEqual(binary.Left, binary.Right, negated: binary.NodeType is ExpressionType.Equal);
        }

        var filter = this.Translate(expression);

        switch (filter)
        {
            case { Must.Count: 1, MustNot.Count: 0, Should.Count: 0 }:
                filter.MustNot.Add(filter.Must[0]);
                filter.Must.RemoveAt(0);
                return filter;

            case { Must.Count: 0, MustNot.Count: 1, Should.Count: 0 }:
                filter.Must.Add(filter.MustNot[0]);
                filter.MustNot.RemoveAt(0);
                return filter;

            case { Must.Count: 0, MustNot.Count: 0, Should.Count: > 0 }:
                filter.MustNot.AddRange(filter.Should);
                filter.Should.Clear();
                return filter;

            default:
                return new Filter { MustNot = { new Condition { Filter = filter } } };
        }
    }

    #endregion Logical operators

    private Filter TranslateMethodCall(MethodCallExpression methodCall)
    {
        return methodCall switch
        {
            // Enumerable.Contains()
            { Method.Name: nameof(Enumerable.Contains), Arguments: [var source, var item] } contains
                when contains.Method.DeclaringType == typeof(Enumerable)
                => this.TranslateContains(source, item),

            // List.Contains()
            {
                Method:
                {
                    Name: nameof(Enumerable.Contains),
                    DeclaringType: { IsGenericType: true } declaringType
                },
                Object: Expression source,
                Arguments: [var item]
            } when declaringType.GetGenericTypeDefinition() == typeof(List<>)
                => this.TranslateContains(source, item),

            // C# 14 made changes to overload resolution to prefer Span-based overloads when those exist ("first-class spans");
            // this makes MemoryExtensions.Contains() be resolved rather than Enumerable.Contains() (see above).
            // MemoryExtensions.Contains() also accepts a Span argument for the source, adding an implicit cast we need to remove.
            // See https://github.com/dotnet/runtime/issues/109757 for more context.
            // Note that MemoryExtensions.Contains has an optional 3rd ComparisonType parameter; we only match when
            // it's null.
            { Method.Name: nameof(MemoryExtensions.Contains), Arguments: [var spanArg, var item, ..] } contains
                when contains.Method.DeclaringType == typeof(MemoryExtensions)
                    && (contains.Arguments.Count is 2
                        || (contains.Arguments.Count is 3 && contains.Arguments[2] is ConstantExpression { Value: null }))
                    && TryUnwrapSpanImplicitCast(spanArg, out var source)
                => this.TranslateContains(source, item),

            _ => throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}")
        };

        static bool TryUnwrapSpanImplicitCast(Expression expression, [NotNullWhen(true)] out Expression? result)
        {
            // Different versions of the compiler seem to generate slightly different expression tree representations for this
            // implicit cast:
            var (unwrapped, castDeclaringType) = expression switch
            {
                UnaryExpression
                {
                    NodeType: ExpressionType.Convert,
                    Method: { Name: "op_Implicit", DeclaringType: { IsGenericType: true } implicitCastDeclaringType },
                    Operand: var operand
                } => (operand, implicitCastDeclaringType),

                MethodCallExpression
                {
                    Method: { Name: "op_Implicit", DeclaringType: { IsGenericType: true } implicitCastDeclaringType },
                    Arguments: [var firstArgument]
                } => (firstArgument, implicitCastDeclaringType),

                _ => (null, null)
            };

            // For the dynamic case, there's a Convert node representing an up-cast to object[]; unwrap that too.
            if (unwrapped is UnaryExpression
                {
                    NodeType: ExpressionType.Convert,
                    Method: null
                } convert
                && convert.Type == typeof(object[]))
            {
                result = convert.Operand;
                return true;
            }

            if (unwrapped is not null
                && castDeclaringType?.GetGenericTypeDefinition() is var genericTypeDefinition
                    && (genericTypeDefinition == typeof(Span<>) || genericTypeDefinition == typeof(ReadOnlySpan<>)))
            {
                result = unwrapped;
                return true;
            }

            result = null;
            return false;
        }
    }

    private Filter TranslateContains(Expression source, Expression item)
    {
        switch (source)
        {
            // Contains over field enumerable
            case var _ when this.TryBindProperty(source, out _):
                // Oddly, in Qdrant, tag list contains is handled using a Match condition, just like equality.
                return this.TranslateEqual(source, item);

            // Contains over inline enumerable
            case NewArrayExpression newArray:
                var elements = new object?[newArray.Expressions.Count];

                for (var i = 0; i < newArray.Expressions.Count; i++)
                {
                    if (newArray.Expressions[i] is not ConstantExpression { Value: var elementValue })
                    {
                        throw new NotSupportedException("Inline array elements must be constants");
                    }

                    elements[i] = elementValue;
                }

                return ProcessInlineEnumerable(elements, item);

            case ConstantExpression { Value: IEnumerable enumerable and not string }:
                return ProcessInlineEnumerable(enumerable, item);

            default:
                throw new NotSupportedException("Unsupported Contains");
        }

        Filter ProcessInlineEnumerable(IEnumerable elements, Expression item)
        {
            if (!this.TryBindProperty(item, out var property))
            {
                throw new NotSupportedException("Unsupported item type in Contains");
            }

            switch (property.Type)
            {
                case var t when t == typeof(string):
                    var strings = new RepeatedStrings();

                    foreach (var value in elements)
                    {
                        strings.Strings.Add(value is string or null
                            ? (string?)value
                            : throw new ArgumentException("Non-string element in string Contains array"));
                    }

                    return new Filter { Must = { new Condition { Field = new FieldCondition { Key = property.StorageName, Match = new Match { Keywords = strings } } } } };

                case var t when t == typeof(int):
                    var ints = new RepeatedIntegers();

                    foreach (var value in elements)
                    {
                        ints.Integers.Add(value is int intValue
                            ? intValue
                            : throw new ArgumentException("Non-int element in string Contains array"));
                    }

                    return new Filter { Must = { new Condition { Field = new FieldCondition { Key = property.StorageName, Match = new Match { Integers = ints } } } } };

                default:
                    throw new NotSupportedException("Contains only supported over array of ints or strings");
            }
        }
    }

    private bool TryBindProperty(Expression expression, [NotNullWhen(true)] out PropertyModel? property)
    {
        var unwrappedExpression = expression;
        while (unwrappedExpression is UnaryExpression { NodeType: ExpressionType.Convert } convert)
        {
            unwrappedExpression = convert.Operand;
        }

        var modelName = unwrappedExpression switch
        {
            // Regular member access for strongly-typed POCO binding (e.g. r => r.SomeInt == 8)
            MemberExpression memberExpression when memberExpression.Expression == this._recordParameter
                => memberExpression.Member.Name,

            // Dictionary lookup for weakly-typed dynamic binding (e.g. r => r["SomeInt"] == 8)
            MethodCallExpression
            {
                Method: { Name: "get_Item", DeclaringType: var declaringType },
                Arguments: [ConstantExpression { Value: string keyName }]
            } methodCall when methodCall.Object == this._recordParameter && declaringType == typeof(Dictionary<string, object?>)
                => keyName,

            _ => null
        };

        if (modelName is null)
        {
            property = null;
            return false;
        }

        if (!this._model.PropertyMap.TryGetValue(modelName, out property))
        {
            throw new InvalidOperationException($"Property name '{modelName}' provided as part of the filter clause is not a valid property name.");
        }

        // Now that we have the property, go over all wrapping Convert nodes again to ensure that they're compatible with the property type
        var unwrappedPropertyType = Nullable.GetUnderlyingType(property.Type) ?? property.Type;
        unwrappedExpression = expression;
        while (unwrappedExpression is UnaryExpression { NodeType: ExpressionType.Convert } convert)
        {
            var convertType = Nullable.GetUnderlyingType(convert.Type) ?? convert.Type;
            if (convertType != unwrappedPropertyType && convertType != typeof(object))
            {
                throw new InvalidCastException($"Property '{property.ModelName}' is being cast to type '{convert.Type.Name}', but its configured type is '{property.Type.Name}'.");
            }

            unwrappedExpression = convert.Operand;
        }

        return true;
    }
}
