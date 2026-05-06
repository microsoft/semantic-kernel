// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
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

#pragma warning disable MEVD9001 // Experimental: filter translation base types

// https://qdrant.tech/documentation/concepts/filtering
internal class QdrantFilterTranslator : FilterTranslatorBase
{
    internal Filter Translate(LambdaExpression lambdaExpression, CollectionModel model)
    {
        var preprocessedExpression = this.PreprocessFilter(lambdaExpression, model, new FilterPreprocessingOptions());

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
                        DateTime v => new Match { Keyword = v.ToString("o") },
                        DateTimeOffset v => new Match { Keyword = v.ToString("o") },
#if NET
                        DateOnly v => new Match { Keyword = v.ToString("O") },
#endif

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

                        DateTime v => new FieldCondition
                        {
                            Key = property.StorageName,
                            DatetimeRange = new DatetimeRange
                            {
                                Gt = comparison.NodeType == ExpressionType.GreaterThan ? Timestamp.FromDateTime(DateTime.SpecifyKind(v, DateTimeKind.Utc)) : null,
                                Gte = comparison.NodeType == ExpressionType.GreaterThanOrEqual ? Timestamp.FromDateTime(DateTime.SpecifyKind(v, DateTimeKind.Utc)) : null,
                                Lt = comparison.NodeType == ExpressionType.LessThan ? Timestamp.FromDateTime(DateTime.SpecifyKind(v, DateTimeKind.Utc)) : null,
                                Lte = comparison.NodeType == ExpressionType.LessThanOrEqual ? Timestamp.FromDateTime(DateTime.SpecifyKind(v, DateTimeKind.Utc)) : null
                            }
                        },

#if NET
                        DateOnly v => new FieldCondition
                        {
                            Key = property.StorageName,
                            DatetimeRange = new DatetimeRange
                            {
                                Gt = comparison.NodeType == ExpressionType.GreaterThan ? Timestamp.FromDateTimeOffset(new DateTimeOffset(v.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero)) : null,
                                Gte = comparison.NodeType == ExpressionType.GreaterThanOrEqual ? Timestamp.FromDateTimeOffset(new DateTimeOffset(v.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero)) : null,
                                Lt = comparison.NodeType == ExpressionType.LessThan ? Timestamp.FromDateTimeOffset(new DateTimeOffset(v.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero)) : null,
                                Lte = comparison.NodeType == ExpressionType.LessThanOrEqual ? Timestamp.FromDateTimeOffset(new DateTimeOffset(v.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero)) : null
                            }
                        },
#endif

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
            // Enumerable.Contains(), List.Contains(), MemoryExtensions.Contains()
            _ when TryMatchContains(methodCall, out var source, out var item)
                => this.TranslateContains(source, item),

            // Enumerable.Any() with a Contains predicate (r => r.Strings.Any(s => array.Contains(s)))
            { Method.Name: nameof(Enumerable.Any), Arguments: [var anySource, LambdaExpression lambda] } any
                when any.Method.DeclaringType == typeof(Enumerable)
                => this.TranslateAny(anySource, lambda),

            _ => throw new NotSupportedException($"Unsupported method call: {methodCall.Method.DeclaringType?.Name}.{methodCall.Method.Name}")
        };
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

    /// <summary>
    /// Translates an Any() call with a Contains predicate, e.g. r.Strings.Any(s => array.Contains(s)).
    /// This checks whether any element in the array field is contained in the given values.
    /// </summary>
    private Filter TranslateAny(Expression source, LambdaExpression lambda)
    {
        // We only support the pattern: r.ArrayField.Any(x => values.Contains(x))
        if (!this.TryBindProperty(source, out var property)
            || lambda.Body is not MethodCallExpression containsCall
            || !TryMatchContains(containsCall, out var valuesExpression, out var itemExpression))
        {
            throw new NotSupportedException("Unsupported method call: Enumerable.Any");
        }

        // Verify that the item is the lambda parameter
        if (itemExpression != lambda.Parameters[0])
        {
            throw new NotSupportedException("Unsupported method call: Enumerable.Any");
        }

        // Extract the values
        IEnumerable values = valuesExpression switch
        {
            NewArrayExpression newArray => ExtractArrayValues(newArray),
            ConstantExpression { Value: IEnumerable enumerable and not string } => enumerable,
            _ => throw new NotSupportedException("Unsupported method call: Enumerable.Any")
        };

        // Generate a Match condition with RepeatedStrings or RepeatedIntegers
        // This works because in Qdrant, matching against an array field with multiple values
        // returns records where ANY element matches ANY of the values
        var elementType = property.Type.IsArray
            ? property.Type.GetElementType()
            : property.Type.IsGenericType && property.Type.GetGenericTypeDefinition() == typeof(List<>)
                ? property.Type.GetGenericArguments()[0]
                : null;

        switch (elementType)
        {
            case var t when t == typeof(string):
                var strings = new RepeatedStrings();

                foreach (var value in values)
                {
                    strings.Strings.Add(value is string or null
                        ? (string?)value
                        : throw new ArgumentException("Non-string element in string Any array"));
                }

                return new Filter { Must = { new Condition { Field = new FieldCondition { Key = property.StorageName, Match = new Match { Keywords = strings } } } } };

            case var t when t == typeof(int):
                var ints = new RepeatedIntegers();

                foreach (var value in values)
                {
                    ints.Integers.Add(value is int intValue
                        ? intValue
                        : throw new ArgumentException("Non-int element in int Any array"));
                }

                return new Filter { Must = { new Condition { Field = new FieldCondition { Key = property.StorageName, Match = new Match { Integers = ints } } } } };

            default:
                throw new NotSupportedException("Any with Contains only supported over array of ints or strings");
        }

        static object?[] ExtractArrayValues(NewArrayExpression newArray)
        {
            var result = new object?[newArray.Expressions.Count];
            for (var i = 0; i < newArray.Expressions.Count; i++)
            {
                if (newArray.Expressions[i] is not ConstantExpression { Value: var elementValue })
                {
                    throw new NotSupportedException("Invalid element in array");
                }

                result[i] = elementValue;
            }

            return result;
        }
    }
}
