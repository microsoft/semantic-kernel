// Copyright (c) Microsoft. All rights reserved.

using System;
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
}
