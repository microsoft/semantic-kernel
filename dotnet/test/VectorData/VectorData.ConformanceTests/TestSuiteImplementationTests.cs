// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using System.Text.RegularExpressions;
using Xunit;

namespace VectorData.ConformanceTests;

/// <summary>
/// A test that ensures that all base test suites are implemented (or explicitly ignored) in provider implementations.
/// Used to make sure that test coverage is complete.
/// </summary>
public abstract class TestSuiteImplementationTests
{
    protected virtual ICollection<Type> IgnoredTestBases { get; } = [];

    [Fact]
    public virtual void All_test_bases_must_be_implemented()
    {
        var concreteTests
            = this.GetType().Assembly.GetTypes()
                .Where(c => c.BaseType != typeof(object) && !c.IsAbstract && (c.IsPublic || c.IsNestedPublic))
                .ToList();

        var nonImplementedBases
            = this.GetBaseTestClasses()
                .Where(t => !this.IgnoredTestBases.Contains(t) && !concreteTests.Any(c => Implements(c, t)))
                .Select(t => t.FullName)
                .ToList();

        Assert.False(
            nonImplementedBases.Count > 0,
            "\r\n-- Missing derived classes for --\r\n" + string.Join(Environment.NewLine, nonImplementedBases));
    }

    // Filter for abstract base types which end with Tests and possibly generic arity (e.g. FooTests`2)
    protected virtual IEnumerable<Type> GetBaseTestClasses()
        => typeof(TestSuiteImplementationTests).Assembly.ExportedTypes
            .Where(t => Regex.IsMatch(t.Name, """Tests(`\d+)?$""") && t.IsAbstract && !t.IsSealed && !t.IsInterface);

    private static bool Implements(Type type, Type interfaceOrBaseType)
        => (type.IsPublic || type.IsNestedPublic) && interfaceOrBaseType.IsGenericTypeDefinition
            ? GetGenericTypeImplementations(type, interfaceOrBaseType).Any()
            : interfaceOrBaseType.IsAssignableFrom(type);

    private static IEnumerable<Type> GetGenericTypeImplementations(Type type, Type interfaceOrBaseType)
    {
        var typeInfo = type.GetTypeInfo();

        if (!typeInfo.IsGenericTypeDefinition)
        {
            var baseTypes = interfaceOrBaseType.IsInterface
                ? typeInfo.ImplementedInterfaces
                : GetBaseTypes(type);
            foreach (var baseType in baseTypes)
            {
                if (baseType.IsGenericType
                    && baseType.GetGenericTypeDefinition() == interfaceOrBaseType)
                {
                    yield return baseType;
                }
            }

            if (type.IsGenericType
                && type.GetGenericTypeDefinition() == interfaceOrBaseType)
            {
                yield return type;
            }
        }
    }

    private static IEnumerable<Type> GetBaseTypes(Type type)
    {
        var t = type.BaseType;

        while (t != null)
        {
            yield return t;

            t = t.BaseType;
        }
    }
}
