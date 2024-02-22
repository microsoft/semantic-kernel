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
        var text = "text";
        var (serviceMock, classificationContent) = GetClassificationServiceMockAndClassificationContent(text);

        // Act
        var result = await TextClassificationExtensions.ClassifyTextAsync(serviceMock.Object, text);

        // Assert
        Assert.Equal(classificationContent, result);
    }

    [Fact]
    public async Task ClassifyTextAsyncItUsesTextClassificationServiceAsync()
    {
        // Arrange
        var text = "text";
        var (serviceMock, _) = GetClassificationServiceMockAndClassificationContent(text);

        // Act
        await TextClassificationExtensions.ClassifyTextAsync(serviceMock.Object, text);

        // Assert
        serviceMock.VerifyAll();
    }

    private static (Mock<ITextClassificationService>, ClassificationContent) GetClassificationServiceMockAndClassificationContent(string text)
    {
        var serviceMock = new Mock<ITextClassificationService>();
        ClassificationContent classificationContent = new(null, text, new Dictionary<string, object?>());
        serviceMock.Setup(x => x.ClassifyTextsAsync(new[] { text }, null, null, default))
            .ReturnsAsync(new List<ClassificationContent> { classificationContent });
        return (serviceMock, classificationContent);
    }
}
