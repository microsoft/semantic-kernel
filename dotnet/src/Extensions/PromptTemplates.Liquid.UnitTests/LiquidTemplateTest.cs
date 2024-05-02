// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.PromptTemplates.Liquid;
using Xunit;
namespace SemanticKernel.Extensions.PromptTemplates.Liquid.UnitTests;
public class LiquidTemplateTest
{
    [Fact]
    public async Task ItRenderChatTestAsync()
    {
        // Arrange
        var liquidTemplatePath = Path.Combine(Directory.GetCurrentDirectory(), "TestData", "chat.txt");
        var liquidTemplate = File.ReadAllText(liquidTemplatePath);

        var config = new PromptTemplateConfig()
        {
            TemplateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat,
            Template = liquidTemplate,
        };

        // create a dynamic customer object
        // customer contains the following properties
        // - firstName
        // - lastName
        // - age
        // - membership
        // - orders []
        //  - name
        //  - description
        var customer = new
        {
            firstName = "John",
            lastName = "Doe",
            age = 30,
            membership = "Gold",
            orders = new[]
            {
                new { name = "apple", description = "2 fuji apples", date = "2024/04/01" },
                new { name = "banana", description = "1 free banana from amazon banana hub", date = "2024/04/03" },
            },
        };

        // create a list of documents
        // documents contains the following properties
        // - id
        // - title
        // - content
        var documents = new[]
        {
            new { id = "1", title = "apple", content = "2 apples"},
            new { id = "2", title = "banana", content = "3 bananas"},
        };

        // create chat history
        // each chat message contains the following properties
        // - role (system, user, assistant)
        // - content

        var chatHistory = new[]
        {
            new { role = "user", content = "When is the last time I bought apple?" },
        };

        var arguments = new KernelArguments()
        {
            { "customer", customer },
            { "documentation", documents },
            { "history", chatHistory },
        };

        var liquidTemplateInstance = new LiquidPromptTemplate(config);

        // Act
        var result = await liquidTemplateInstance.RenderAsync(new Kernel(), arguments);

        // Assert
        await VerifyXunit.Verifier.Verify(result);
    }

    [Fact]
    public async Task ItRendersVariablesAsync()
    {
        // Arrange
        var template = "My name is {{person.name}} and my email address is {{email}}";

        var config = new PromptTemplateConfig()
        {
            TemplateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat,
            Template = template,
        };

        var arguments = new KernelArguments()
        {
            { "person", new { name = "John Doe" } },
            { "email", "123456@gmail.com"}
        };

        var liquidTemplateInstance = new LiquidPromptTemplate(config);

        // Act
        var result = await liquidTemplateInstance.RenderAsync(new Kernel(), arguments);

        // Assert
        var expected = "My name is John Doe and my email address is 123456@gmail.com";
        Assert.Equal(expected, result);
    }

    [Fact]
    public async Task ItUsesDefaultValuesAsync()
    {
        // Arrange
        var template = "Foo {{bar}} {{baz}}{{null}}{{empty}}";
        var config = new PromptTemplateConfig()
        {
            TemplateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat,
            Template = template,
        };

        config.InputVariables.Add(new() { Name = "bar", Description = "Bar", Default = "Bar" });
        config.InputVariables.Add(new() { Name = "baz", Description = "Baz", Default = "Baz" });
        config.InputVariables.Add(new() { Name = "null", Description = "Null", Default = null });
        config.InputVariables.Add(new() { Name = "empty", Description = "empty", Default = string.Empty });

        var target = new LiquidPromptTemplate(config);

        // Act
        var prompt = await target.RenderAsync(new Kernel(), new KernelArguments());

        // Assert   
        Assert.Equal("Foo Bar Baz", prompt);
    }

    [Fact]
    public async Task ItRendersConditionalStatementsAsync()
    {
        // Arrange
        var template = "Foo {% if bar %}{{bar}}{% else %}No Bar{% endif %}";
        var promptConfig = new PromptTemplateConfig()
        {
            TemplateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat,
            Template = template,
        };

        var target = new LiquidPromptTemplate(promptConfig);

        // Act on positive case
        var arguments = new KernelArguments();
        var kernel = new Kernel();
        arguments["bar"] = "Bar";
        var prompt = await target.RenderAsync(kernel, arguments);

        // Assert   
        Assert.Equal("Foo Bar", prompt);

        // Act on negative case
        arguments["bar"] = null;
        prompt = await target.RenderAsync(kernel, arguments);

        // Assert   
        Assert.Equal("Foo No Bar", prompt);
    }

    [Fact]
    public async Task ItRendersLoopsAsync()
    {
        // Arrange
        var template = "List: {% for item in items %}{{item}}{% endfor %}";
        var promptConfig = new PromptTemplateConfig()
        {
            TemplateFormat = LiquidPromptTemplateFactory.LiquidTemplateFormat,
            Template = template,
        };

        var target = new LiquidPromptTemplate(promptConfig);
        var arguments = new KernelArguments();
        var kernel = new Kernel();
        arguments["items"] = new List<string> { "item1", "item2", "item3" };

        // Act
        var prompt = await target.RenderAsync(kernel, arguments);

        // Assert   
        Assert.Equal("List: item1item2item3", prompt);
    }
}
