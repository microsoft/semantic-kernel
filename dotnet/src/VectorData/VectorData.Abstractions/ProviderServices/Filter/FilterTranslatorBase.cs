// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Linq.Expressions;
using System.Reflection;

namespace Microsoft.Extensions.VectorData.ProviderServices.Filter;

/// <summary>
/// Base class for filter translators used by vector data connectors.
/// Provides common functionality for preprocessing filter expressions and matching common patterns.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public abstract class FilterTranslatorBase
{
    /// <summary>
    /// The collection model for the current translation operation.
    /// </summary>
    protected CollectionModel Model { get; private set; } = null!;

    /// <summary>
    /// The parameter expression representing the record in the filter lambda.
    /// </summary>
    protected ParameterExpression RecordParameter { get; private set; } = null!;

    /// <summary>
    /// Preprocesses the filter expression before translation.
    /// Sets <see cref="Model"/> and <see cref="RecordParameter"/>, runs the preprocessing visitor,
    /// and returns the preprocessed expression.
    /// </summary>
    /// <param name="lambdaExpression">The filter lambda expression to preprocess.</param>
    /// <param name="model">The collection model containing property information.</param>
    /// <param name="options">Options controlling the preprocessing behavior.</param>
    /// <returns>The preprocessed expression ready for translation.</returns>
    protected Expression PreprocessFilter(LambdaExpression lambdaExpression, CollectionModel model, FilterPreprocessingOptions options)
    {
        this.Model = model;
        this.RecordParameter = lambdaExpression.Parameters[0];

        var preprocessor = new FilterTranslationPreprocessor(options.SupportsParameterization);
        return preprocessor.Preprocess(lambdaExpression.Body);
    }

    /// <summary>
    /// Tries to match a Contains method call expression and extract the source collection and item expressions.
    /// </summary>
    /// <param name="methodCall">The method call expression to match.</param>
    /// <param name="source">When successful, the source collection expression.</param>
    /// <param name="item">When successful, the item expression being searched for.</param>
    /// <returns><see langword="true"/> if the expression is a recognized Contains pattern; otherwise, <see langword="false"/>.</returns>
    protected static bool TryMatchContains(
        MethodCallExpression methodCall,
        [NotNullWhen(true)] out Expression? source,
        [NotNullWhen(true)] out Expression? item)
    {
        switch (methodCall)
        {
            // Enumerable.Contains()
            case { Method.Name: nameof(Enumerable.Contains), Arguments: [var src, var itm] }
                when methodCall.Method.DeclaringType == typeof(Enumerable):
                source = src;
                item = itm;
                return true;

            // List<T>.Contains()
            case
            {
                Method:
                {
                    Name: nameof(Enumerable.Contains),
                    DeclaringType: { IsGenericType: true } declaringType
                },
                Object: Expression src,
                Arguments: [var itm]
            } when declaringType.GetGenericTypeDefinition() == typeof(List<>):
                source = src;
                item = itm;
                return true;

            // C# 14 made changes to overload resolution to prefer Span-based overloads when those exist ("first-class spans");
            // this makes MemoryExtensions.Contains() be resolved rather than Enumerable.Contains() (see above).
            // MemoryExtensions.Contains() also accepts a Span argument for the source, adding an implicit cast we need to remove.
            // See https://github.com/dotnet/runtime/issues/109757 for more context.
            // Note that MemoryExtensions.Contains has an optional 3rd ComparisonType parameter; we only match when
            // it's null.
            case { Method.Name: nameof(MemoryExtensions.Contains), Arguments: [var spanArg, var itm, ..] }
                when methodCall.Method.DeclaringType == typeof(MemoryExtensions)
                    && (methodCall.Arguments.Count is 2
                        || (methodCall.Arguments.Count is 3 && methodCall.Arguments[2] is ConstantExpression { Value: null }))
                    && TryUnwrapSpanImplicitCast(spanArg, out var src):
                source = src;
                item = itm;
                return true;

            default:
                source = null;
                item = null;
                return false;
        }
    }

    /// <summary>
    /// Tries to bind an expression to a property in the collection model.
    /// </summary>
    /// <param name="expression">The expression to bind.</param>
    /// <param name="propertyModel">When successful, the property model that was bound.</param>
    /// <returns><see langword="true"/> if the expression was successfully bound to a property; otherwise, <see langword="false"/>.</returns>
    protected virtual bool TryBindProperty(Expression expression, [NotNullWhen(true)] out PropertyModel? propertyModel)
    {
        var unwrappedExpression = expression;
        while (unwrappedExpression is UnaryExpression { NodeType: ExpressionType.Convert } convert)
        {
            unwrappedExpression = convert.Operand;
        }

        var modelName = unwrappedExpression switch
        {
            // Regular member access for strongly-typed POCO binding (e.g. r => r.SomeInt == 8)
            MemberExpression memberExpression when memberExpression.Expression == this.RecordParameter
                => memberExpression.Member.Name,

            // Dictionary lookup for weakly-typed dynamic binding (e.g. r => r["SomeInt"] == 8)
            MethodCallExpression
            {
                Method: { Name: "get_Item", DeclaringType: var declaringType },
                Arguments: [ConstantExpression { Value: string keyName }]
            } methodCall when methodCall.Object == this.RecordParameter && declaringType == typeof(Dictionary<string, object?>)
                => keyName,

            _ => null
        };

        if (modelName is null)
        {
            propertyModel = null;
            return false;
        }

        if (!this.Model.PropertyMap.TryGetValue(modelName, out propertyModel))
        {
            throw new InvalidOperationException($"Property name '{modelName}' provided as part of the filter clause is not a valid property name.");
        }

        // Now that we have the property, go over all wrapping Convert nodes again to ensure that they're compatible with the property type
        var unwrappedPropertyType = Nullable.GetUnderlyingType(propertyModel.Type) ?? propertyModel.Type;
        unwrappedExpression = expression;
        while (unwrappedExpression is UnaryExpression { NodeType: ExpressionType.Convert } convert)
        {
            var convertType = Nullable.GetUnderlyingType(convert.Type) ?? convert.Type;
            if (convertType != unwrappedPropertyType && convertType != typeof(object))
            {
                throw new InvalidCastException($"Property '{propertyModel.ModelName}' is being cast to type '{convert.Type.Name}', but its configured type is '{propertyModel.Type.Name}'.");
            }

            unwrappedExpression = convert.Operand;
        }

        return true;
    }

    /// <summary>
    /// Tries to unwrap an implicit cast to Span or ReadOnlySpan that may be present in expressions
    /// when C# 14's first-class span support causes MemoryExtensions methods to be resolved.
    /// </summary>
    /// <param name="expression">The expression to unwrap.</param>
    /// <param name="result">When successful, the unwrapped expression.</param>
    /// <returns><see langword="true"/> if a span implicit cast was unwrapped; otherwise, <see langword="false"/>.</returns>
    protected static bool TryUnwrapSpanImplicitCast(Expression expression, [NotNullWhen(true)] out Expression? result)
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

            // After the preprocessor runs, the Convert node may have Method: null because the visitor
            // recreates the UnaryExpression with a different operand type (QueryParameterExpression).
            // Handle this case by checking if the target type is Span<T> or ReadOnlySpan<T>.
            UnaryExpression
            {
                NodeType: ExpressionType.Convert,
                Method: null,
                Type: { IsGenericType: true } targetType,
                Operand: var operand
            } when targetType.GetGenericTypeDefinition() is var gtd
                && (gtd == typeof(Span<>) || gtd == typeof(ReadOnlySpan<>))
                => (operand, targetType),

            _ => (null, null)
        };

        // For the dynamic case, there's a Convert node representing an up-cast to object[]; unwrap that too.
        // Also handle cases where the preprocessor adds a Convert node back to the array type.
        while (unwrapped is UnaryExpression
            {
                NodeType: ExpressionType.Convert,
                Method: null,
                Operand: var innerOperand
            })
        {
            unwrapped = innerOperand;
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

    #region FilterTranslationPreprocessor

    /// <summary>
    /// A processor for user-provided filter expressions which performs various common transformations before actual translation takes place.
    /// </summary>
    private sealed class FilterTranslationPreprocessor : ExpressionVisitor
    {
        private readonly bool _supportsParameterization;
        private List<string>? _parameterNames;

        internal FilterTranslationPreprocessor(bool supportsParameterization)
        {
            this._supportsParameterization = supportsParameterization;
        }

        internal Expression Preprocess(Expression node)
        {
            if (this._supportsParameterization)
            {
                this._parameterNames = [];
            }

            return this.Visit(node);
        }

        /// <inheritdoc />
        protected override Expression VisitMember(MemberExpression node)
        {
            var visited = (MemberExpression)base.VisitMember(node);

            // This identifies field and property access over constants, which can be evaluated immediately.
            // This covers captured variables, since those are actually member accesses over compiled-generated closure types:
            // var x = 8;
            // _ = await collection.SearchAsync(vector, top: 3, new() { Filter = r => r.Int == x });
            //
            // This also covers member variables:
            // _ = await collection.SearchAsync(vector, top: 3, new() { Filter = r => r.Int == this._x });
            // ... as "this" here is represented by a ConstantExpression node in the tree.
            //
            // Some databases - mostly relational ones - support out-of-band parameters which can be referenced via placeholders
            // from the query itself. For those databases, we transform the member access to QueryParameterExpression (this simplifies things for those
            // connectors, and centralizes the pattern matching in a single centralized place).
            // For databases which don't support parameters, we simply inline the evaluated member access as a constant in the tree, so that translators don't
            // even need to be aware of it.

            // Evaluate the MemberExpression to get the actual value, either for instance members (expression is a ConstantExpression) or for
            // static members (expression is null).
            object? baseValue;
            switch (visited.Expression)
            {
                // Member access over constant (i.e. instance members)
                case ConstantExpression { Value: var v }:
                    baseValue = v;
                    break;

                // Member constant over null (i.e. static members)
                case null:
                    baseValue = null;
                    break;

                // Member constant over something that has already been parameterized (i.e. nested member access, e.g. r=> r.Int == this.SomeWrapper.Something)
                case QueryParameterExpression p:
                    baseValue = p.Value;

                    // The previous parameter is getting replaced by the new one we're creating here, so remove its name from the list of parameter names.
                    this._parameterNames!.Remove(p.Name);
                    break;

                default:
                    return visited;
            }

            object? evaluatedValue;

            var memberInfo = visited.Member;

            switch (memberInfo)
            {
                case FieldInfo fieldInfo:
                    evaluatedValue = fieldInfo.GetValue(baseValue);
                    break;

                case PropertyInfo { GetMethod.IsStatic: false } propertyInfo when baseValue is null:
                    throw new InvalidOperationException($"Cannot access member '{propertyInfo.Name}' on null object.");

                case PropertyInfo propertyInfo:
                    evaluatedValue = propertyInfo.GetValue(baseValue);
                    break;
                default:
                    return visited;
            }

            // Inline the evaluated value (if the connector doesn't support parameterization, or if the field is readonly),
            if (!this._supportsParameterization)
            {
                return Expression.Constant(evaluatedValue, visited.Type);
            }

            // Otherwise, transform the node to a QueryParameterExpression which the connector will then translate to a parameter (e.g. SqlParameter).

            // TODO: Share the same parameter when it references the same captured value

            // Make sure parameter names are unique.
            var origName = memberInfo.Name;
            var name = origName;
            for (var i = 0; this._parameterNames!.Contains(name); i++)
            {
                name = $"{origName}_{i}";
            }
            this._parameterNames.Add(name);

            return new QueryParameterExpression(name, evaluatedValue, visited.Type);
        }

        /// <inheritdoc />
        protected override Expression VisitNew(NewExpression node)
        {
            var visited = (NewExpression)base.VisitNew(node);

            // Recognize certain well-known constructors where we can evaluate immediately, converting the NewExpression to a ConstantExpression.
            // This is particularly useful for converting inline instantiation of DateTime and DateTimeOffset to constants, which can then be easily translated.
            switch (visited.Constructor)
            {
                case ConstructorInfo constructor when constructor.DeclaringType == typeof(DateTimeOffset) || constructor.DeclaringType == typeof(DateTime):
                    var constantArguments = new object?[visited.Arguments.Count];

                    // We first do a fast path to check if all arguments are constants; this catches the common case of e.g. new DateTime(2023, 10, 1).
                    // If an argument isn't a constant (e.g. new DateTimeOffset(..., TimeSpan.FromHours(2))), we fall back to trying the LINQ interpreter
                    // as a general-purpose expression evaluator - but note that this is considerably slower.
                    for (var i = 0; i < visited.Arguments.Count; i++)
                    {
                        if (visited.Arguments[i] is ConstantExpression constantArgument)
                        {
                            constantArguments[i] = constantArgument.Value;
                        }
                        else
                        {
                            // There's a non-constant argument - try the LINQ interpreter.
#pragma warning disable CA1031 // Do not catch general exception types
                            try
                            {
                                var evaluated = Expression.Lambda<Func<object>>(Expression.Convert(visited, typeof(object)))
#if NET
                                    .Compile(preferInterpretation: true)
#else
                                    .Compile()
#endif
                                    .Invoke();

                                return Expression.Constant(evaluated, constructor.DeclaringType);
                            }
                            catch
                            {
                                return visited;
                            }
#pragma warning restore CA1031
                        }
                    }

                    var constantValue = constructor.Invoke(constantArguments);
                    return Expression.Constant(constantValue, constructor.DeclaringType);
            }

            return visited;
        }
    }

    #endregion FilterTranslationPreprocessor
}
