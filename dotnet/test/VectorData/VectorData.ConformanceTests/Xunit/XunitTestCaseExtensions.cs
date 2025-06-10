// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using Xunit.Abstractions;
using Xunit.Sdk;

namespace VectorData.ConformanceTests.Xunit;

public static class XunitTestCaseExtensions
{
    private static readonly ConcurrentDictionary<string, List<IAttributeInfo>> s_typeAttributes = new();
    private static readonly ConcurrentDictionary<string, List<IAttributeInfo>> s_assemblyAttributes = new();

    public static async ValueTask<bool> TrySkipAsync(XunitTestCase testCase, IMessageBus messageBus)
    {
        var method = testCase.Method;
        var type = testCase.TestMethod.TestClass.Class;
        var assembly = type.Assembly;

        var skipReasons = new List<string>();
        var attributes =
            s_assemblyAttributes.GetOrAdd(
                    assembly.Name,
                    a => assembly.GetCustomAttributes(typeof(ITestCondition)).ToList())
                .Concat(
                    s_typeAttributes.GetOrAdd(
                        type.Name,
                        t => type.GetCustomAttributes(typeof(ITestCondition)).ToList()))
                .Concat(method.GetCustomAttributes(typeof(ITestCondition)))
                .OfType<ReflectionAttributeInfo>()
                .Select(attributeInfo => (ITestCondition)attributeInfo.Attribute);

        foreach (var attribute in attributes)
        {
            if (!await attribute.IsMetAsync())
            {
                skipReasons.Add(attribute.SkipReason);
            }
        }

        if (skipReasons.Count > 0)
        {
            messageBus.QueueMessage(
                new TestSkipped(new XunitTest(testCase, testCase.DisplayName), string.Join(Environment.NewLine, skipReasons)));

            return true;
        }

        return false;
    }
}
