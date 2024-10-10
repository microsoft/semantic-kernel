// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using HandlebarsDotNet;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars.Helpers;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.PromptTemplates.Handlebars.Helpers;

public class KernelHelperUtilsTests
{
    [Fact]
    public void ItRegistersHelperWhenNameIsUnique()
    {
        // Arrange  
        var handlebarsInstance = HandlebarsDotNet.Handlebars.Create();
        string helperName = "uniqueHelper";
        static object helper(Context context, Arguments arguments) => "Unique Helper Output";

        // Act  
        KernelHelpersUtils.RegisterHelperSafe(handlebarsInstance, helperName, (HandlebarsReturnHelper)helper);

        // Assert  
        Assert.True(handlebarsInstance.Configuration.Helpers.ContainsKey(helperName));
    }

    [Fact]
    public void ItThrowsInvalidOperationExceptionWhenNameIsAlreadyRegistered()
    {
        // Arrange  
        var handlebarsInstance = HandlebarsDotNet.Handlebars.Create();
        string helperName = "alreadyRegisteredHelper";
        object helper1(Context context, Arguments arguments) => "Helper 1 Output";
        object helper2(Context context, Arguments arguments) => "Helper 2 Output";
        handlebarsInstance.RegisterHelper(helperName, (HandlebarsReturnHelper)helper1);

        // Act & Assert  
        Assert.Throws<InvalidOperationException>(() => KernelHelpersUtils.RegisterHelperSafe(handlebarsInstance, helperName, (HandlebarsReturnHelper)helper2));
    }

    [Theory]
    [InlineData(null, false)]
    [InlineData(typeof(string), false)]
    [InlineData(typeof(nuint), true)]
    [InlineData(typeof(nint), true)]
    [InlineData(typeof(sbyte), true)]
    [InlineData(typeof(short), true)]
    [InlineData(typeof(int), true)]
    [InlineData(typeof(long), true)]
    [InlineData(typeof(byte), true)]
    [InlineData(typeof(ushort), true)]
    [InlineData(typeof(uint), true)]
    [InlineData(typeof(ulong), true)]
    [InlineData(typeof(double), true)]
    [InlineData(typeof(float), true)]
    [InlineData(typeof(decimal), true)]
    public void IsNumericTypeWorksCorrectly(Type? type, bool expectedResult)
    {
        Assert.Equal(expectedResult, KernelHelpersUtils.IsNumericType(type));
    }

    [Theory]
    [MemberData(nameof(NumberInputs))]
    public void TryParseAnyNumberWorksCorrectly(string number, bool expectedResult)
    {
        Assert.Equal(expectedResult, KernelHelpersUtils.TryParseAnyNumber(number));
    }

    public static TheoryData<string, bool> NumberInputs => new()
    {
        { 1234567890123456789L.ToString(CultureInfo.InvariantCulture), true },
        { 9876543210987654321UL.ToString(CultureInfo.InvariantCulture), true },
        { 123.456.ToString(CultureInfo.InvariantCulture), true },
        { 123456789.0123456789m.ToString(CultureInfo.InvariantCulture), true },
        { "test", false },
    };
}
