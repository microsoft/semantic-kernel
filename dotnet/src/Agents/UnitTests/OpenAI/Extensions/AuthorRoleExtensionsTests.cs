// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Assistants;
using Xunit;
using KernelExtensions = Microsoft.SemanticKernel.Agents.OpenAI;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit testing of <see cref="KernelExtensions"/>.
/// </summary>
public class AuthorRoleExtensionsTests
{
    /// <summary>
    /// Verify function lookup using KernelExtensions.
    /// </summary>
    [Fact]
    public void VerifyToMessageRole()
    {
        this.VerifyRoleConversion(AuthorRole.Assistant, MessageRole.Assistant);
        this.VerifyRoleConversion(AuthorRole.User, MessageRole.User);

        // Conversion isn't designed to, and won't, encounter these roles; however,
        // this is defined the behavior:
        this.VerifyRoleConversion(AuthorRole.System, MessageRole.Assistant);
        this.VerifyRoleConversion(AuthorRole.Tool, MessageRole.Assistant);
    }

    private void VerifyRoleConversion(AuthorRole inputRole, MessageRole expectedRole)
    {
        // Arrange
        MessageRole convertedRole = inputRole.ToMessageRole();

        // Assert
        Assert.Equal(expectedRole, convertedRole);
    }
}
