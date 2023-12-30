// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Gemini.Core;
using Xunit;

namespace SemanticKernel.Connectors.Gemini.UnitTests.Core;

public sealed class GeminiChatRoleTest
{
    [Fact]
    public void FromAuthorRoleShouldReturnModelWhenPassedAssistantRole()
    {
        // Arrange
        var role = AuthorRole.Assistant;

        // Act
        string result = GeminiChatRole.FromAuthorRole(role);

        // Assert
        Assert.Equal(GeminiChatRole.Assistant, result);
    }

    [Fact]
    public void FromAuthorRoleShouldReturnUserWhenPassedSystemRole()
    {
        // Arrange
        var role = AuthorRole.System;

        // Act
        string result = GeminiChatRole.FromAuthorRole(role);

        // Assert
        Assert.Equal(GeminiChatRole.User, result);
    }

    [Fact]
    public void FromAuthorRoleShouldReturnModelWhenPassedToolRole()
    {
        // Arrange
        var role = AuthorRole.Tool;

        // Act
        string result = GeminiChatRole.FromAuthorRole(role);

        // Assert
        Assert.Equal(GeminiChatRole.Assistant, result);
    }

    [Fact]
    public void FromAuthorRoleShouldReturnUserWhenPassedUserRole()
    {
        // Arrange
        var role = AuthorRole.User;

        // Act
        string result = GeminiChatRole.FromAuthorRole(role);

        // Assert
        Assert.Equal(GeminiChatRole.User, result);
    }

    [Fact]
    public void FromAuthorRoleShouldThrowExceptionWhenPassedUnknownRole()
    {
        // Arrange
        var role = new AuthorRole("unknown");

        // Assert
        Assert.Throws<ArgumentException>(() => GeminiChatRole.FromAuthorRole(role));
    }

    [Fact]
    public void ToAuthorRoleShouldReturnAssistantWhenPassedAssistant()
    {
        // Arrange
        string role = GeminiChatRole.Assistant;

        // Act
        var result = GeminiChatRole.ToAuthorRole(role);

        // Assert
        Assert.Equal(AuthorRole.Assistant, result);
    }

    [Fact]
    public void ToAuthorRoleShouldReturnUserWhenPassedUser()
    {
        // Arrange
        string role = GeminiChatRole.User;

        // Act
        var result = GeminiChatRole.ToAuthorRole(role);

        // Assert
        Assert.Equal(AuthorRole.User, result);
    }

    [Fact]
    public void ToAuthorRoleShouldThrowExceptionWhenPassedUnknownRole()
    {
        // Arrange
        string role = "unknown";

        // Assert
        Assert.Throws<ArgumentException>(() => GeminiChatRole.ToAuthorRole(role));
    }
}
