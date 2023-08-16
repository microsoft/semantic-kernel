// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.MultiConnector.PromptSettings;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion;

public class PromptTransformTests
{
    [Fact]
    public void TestDefaultInterpolation()
    {
        var transform = new PromptTransform { Template = "Hello {0}, {name}!" };
        var result = transform.DefaultTransform("ChatGPT", new Dictionary<string, object> { { "name", "User" } });

        Assert.Equal("Hello ChatGPT, User!", result);
    }

    [Fact]
    public void TestInterpolateKeys()
    {
        var transform = new PromptTransform { Template = "Hello {name}!" };
        var result = transform.InterpolateKeys(transform.Template, new Dictionary<string, object> { { "name", "ChatGPT" } });

        Assert.Equal("Hello ChatGPT!", result);
    }

    [Fact]
    public void TestInterpolateFormattable()
    {
        var transform = new PromptTransform { Template = "Hello {name}!" };
        var result = transform.InterpolateFormattable(transform.Template, new Dictionary<string, object> { { "name", "ChatGPT" } });

        Assert.Equal("Hello ChatGPT!", result);
    }

    [Fact]
    public void TestInterpolateFormattableMixedFormat()
    {
        var transform = new PromptTransform { Template = "Hello {0}, {name}!" };
        var result = transform.InterpolateFormattable(transform.Template, new Dictionary<string, object> { { "name", "ChatGPT" } });

        Assert.Equal("Hello {0}, ChatGPT!", result);
    }

    [Fact]
    public void TestInterpolateDynamicLinqExpression()
    {
        var transform = new PromptTransform { Template = "Hello {name.Length}!" };
        var result = transform.InterpolateDynamicLinqExpression(transform.Template, new Dictionary<string, object> { { "name", "ChatGPT" } });

        Assert.Equal("Hello 7!", result);
    }

    [Fact]
    public void TestInterpolationPerformance()
    {
        var transform = new PromptTransform { Template = "Hello {0}, {name}!" };

        var stopwatch = Stopwatch.StartNew();
        for (int i = 0; i < 10000; i++)
        {
            transform.DefaultTransform("ChatGPT", new Dictionary<string, object> { { "name", "User" } });
        }

        stopwatch.Stop();

        Assert.True(stopwatch.ElapsedMilliseconds < 1000, $"Performance test failed. Elapsed time: {stopwatch.ElapsedMilliseconds} ms");
    }

    [Fact]
    public void TestRelativePerformanceOnSimpleTemplate()
    {
        var transform = new PromptTransform { Template = "Hello {name}! Today is {day}. Your order {orderId} will be delivered in {daysToDelivery} days." };

        string name = "ChatGPT";
        string day = "Monday";
        string orderId = "XYZ1234";
        var daysToDelivery = 3;

        var interpolatedTemplate = $"Hello {name}! Today is {day}. Your order {orderId} will be delivered in {daysToDelivery} days.";

        var values = new Dictionary<string, object>
        {
            { nameof(name), name },
            { nameof(day), day },
            { nameof(orderId), orderId },
            { nameof(daysToDelivery), daysToDelivery }
        };

        // Warm-up calls
        var resultKeys = transform.InterpolateKeys(transform.Template, values);
        Assert.Equal(interpolatedTemplate, resultKeys);
        var resultFormattable = transform.InterpolateFormattable(transform.Template, values);
        Assert.Equal(interpolatedTemplate, resultFormattable);
        var resultDynamicLinq = transform.InterpolateDynamicLinqExpression(transform.Template, values);
        Assert.Equal(interpolatedTemplate, resultDynamicLinq);

        var stopwatchKeys = Stopwatch.StartNew();
        for (int i = 0; i < 10000; i++)
        {
            transform.InterpolateKeys(transform.Template, values);
        }

        stopwatchKeys.Stop();

        var stopwatchFormattable = Stopwatch.StartNew();
        for (int i = 0; i < 10000; i++)
        {
            transform.InterpolateFormattable(transform.Template, values);
        }

        stopwatchFormattable.Stop();

        var stopwatchDynamicLinq = Stopwatch.StartNew();
        for (int i = 0; i < 10000; i++)
        {
            transform.InterpolateDynamicLinqExpression(transform.Template, values);
        }

        stopwatchDynamicLinq.Stop();

        // You can check these values in debug or log them as needed
        long keysDuration = stopwatchKeys.ElapsedMilliseconds;
        long formattableDuration = stopwatchFormattable.ElapsedMilliseconds;
        long dynamicLinqDuration = stopwatchDynamicLinq.ElapsedMilliseconds;

        var maxMultiplier = 5;

        Assert.True(formattableDuration <= maxMultiplier * keysDuration, $"Relative performance test failed. InterpolateKeys: {keysDuration}ms, InterpolateFormattableExpression: {formattableDuration}ms");
        Assert.True(dynamicLinqDuration <= maxMultiplier * keysDuration, $"Relative performance test failed. InterpolateKeys: {keysDuration}ms, dynamicLinqDuration: {dynamicLinqDuration}ms");
    }

    [Fact]
    public void TestFormattableFeatures()
    {
        var someUser = this.GetSampleUser();

        // Flattening the hierarchy for formattable method
        var data = new Dictionary<string, object>
        {
            { "FirstName", someUser.FirstName },
            { "LastName", someUser.LastName },
            { "DateOfBirth", someUser.DateOfBirth },
            { "City", someUser.UserAddress.City },
            { "Country", someUser.UserAddress.Country }
        };

        var template = "Hello {FirstName}, born on {DateOfBirth:yyyy-MM-dd} in {City}, {Country}. Day of birth: {DateOfBirth:dddd}.";
        var interpolatedTemplate = FormattableString.Invariant($"Hello {someUser.FirstName}, born on {someUser.DateOfBirth:yyyy-MM-dd} in {someUser.UserAddress.City}, {someUser.UserAddress.Country}. Day of birth: {someUser.DateOfBirth:dddd}.");

        var transform = new PromptTransform { Template = template };
        var result = transform.InterpolateFormattable(transform.Template, data);

        Assert.Equal(interpolatedTemplate, result);
    }

    [Fact]
    public void TestDynamicLinqHierarchicalInterpolation()
    {
        var someUser = this.GetSampleUser();
        var data = new Dictionary<string, object> { { nameof(someUser), someUser } }; // Hierarchical data

        var template = "Hello {someUser.FirstName} {someUser.LastName}! Born on {someUser.DateOfBirth.Year} in {someUser.UserAddress.City}, {someUser.UserAddress.Country}.";
        var interpolatedTemplate = $"Hello {someUser.FirstName} {someUser.LastName}! Born on {someUser.DateOfBirth.Year} in {someUser.UserAddress.City}, {someUser.UserAddress.Country}.";

        var transform = new PromptTransform { Template = template };
        var result = transform.InterpolateDynamicLinqExpression(transform.Template, data);

        Assert.Equal(interpolatedTemplate, result);
    }

    [Fact]
    public void TestDynamicLinqAdvancedFeatures()
    {
        var transform = new PromptTransform { Template = "{name.Length > 5 ? name.ToUpper() : name.ToLower()}" };
        var resultForLongName = transform.InterpolateDynamicLinqExpression(transform.Template, new Dictionary<string, object> { { "name", "ChatGPT" } });
        var resultForShortName = transform.InterpolateDynamicLinqExpression(transform.Template, new Dictionary<string, object> { { "name", "Bot" } });

        Assert.Equal("CHATGPT", resultForLongName);
        Assert.Equal("bot", resultForShortName);
    }

    private User GetSampleUser()
    {
        return new User
        {
            FirstName = "John",
            LastName = "Doe",
            DateOfBirth = new DateTime(1990, 1, 1),
            UserAddress = new Address
            {
                City = "New York",
                Country = "USA"
            }
        };
    }
}

public class User
{
    public string FirstName { get; set; }
    public string LastName { get; set; }
    public DateTime DateOfBirth { get; set; }
    public Address UserAddress { get; set; }
}

public class Address
{
    public string City { get; set; }
    public string Country { get; set; }
}
