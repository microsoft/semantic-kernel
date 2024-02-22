// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.TextClassification;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.AI.TextClassification;

public sealed class TextClassificationExtensionsTests
{
    [Fact]
    public async Task ClassifyTextAsyncItReturnsClassificationContentAsync()
    {
        // Arrange
        var serviceMock = new Mock<ITextClassificationService>();
        var text = "text";
        var classificationContent = new ClassificationContent(null, text, new Dictionary<string, object?>());
        serviceMock.Setup(x => x.ClassifyTextAsync(new[] { text }, null, null, default))
            .ReturnsAsync(new List<ClassificationContent> { classificationContent });

        // Act
        var result = await TextClassificationExtensions.ClassifyTextAsync(serviceMock.Object, text);

        // Assert
        Assert.Equal(classificationContent, result);
    }

    [Fact]
    public async Task ClassifyTextAsyncItUsesTextClassificationServiceAsync()
    {
        // Arrange
        var serviceMock = new Mock<ITextClassificationService>();
        var text = "text";
        var classificationContent = new ClassificationContent(null, text, new Dictionary<string, object?>());
        serviceMock.Setup(x => x.ClassifyTextAsync(new[] { text }, null, null, default))
            .ReturnsAsync(new List<ClassificationContent> { classificationContent });

        // Act
        await TextClassificationExtensions.ClassifyTextAsync(serviceMock.Object, text);

        // Assert
        serviceMock.VerifyAll();
    }
}
