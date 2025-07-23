// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Immutable;
using System.IO;
using Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows;

public sealed class WorkflowValidationTests(ITestOutputHelper output) : WorkflowTest(output)
{
    [Fact]
    public void VerifyInvalidStreamFailure()
    {
        using StringReader reader = new(Workflows.SimpleWorkflow);
        reader.Close();
        ObjectModelBuilder.TryValidate(reader, out ImmutableArray<ValidationFailure> failures);
        DumpFailures(failures);
        Assert.Single(failures);
        Assert.IsType<ExceptionValidationFailure>(failures[0]);
    }

    [Theory]
    [InlineData(nameof(Workflows.EmptyWorkflow))]
    [InlineData(nameof(Workflows.OnlyComment))]
    [InlineData(nameof(Workflows.JsonExpression))]
    [InlineData(nameof(Workflows.InvalidYaml))]
    public void VerifyDeserializationFailure(string invalidYaml)
    {
        ImmutableArray<ValidationFailure> failures = Validate(invalidYaml, expectValid: false);
        Assert.Single(failures);
        Assert.IsType<ExceptionValidationFailure>(failures[0]);
    }

    [Theory]
    [InlineData(nameof(Workflows.NotWorkflow), 1)]
    public void VerifyDefinitionFailure(string invalidYaml, int expectedFailureCount)
    {
        ImmutableArray<ValidationFailure> failures = Validate(invalidYaml, expectValid: false);
        Assert.Equal(expectedFailureCount, failures.Length);
    }

    private static ImmutableArray<ValidationFailure> Validate(string workflowDefinition, bool expectValid = true)
    {
        using StringReader reader = new(GetWorkflowDefinition(workflowDefinition));
        bool isValid = ObjectModelBuilder.TryValidate(reader, out ImmutableArray<ValidationFailure> failures);
        Assert.Equal(expectValid, isValid);
        DumpFailures(failures);
        return failures;
    }

    private static void DumpFailures(ImmutableArray<ValidationFailure> failures)
    {
        if (failures.IsEmpty)
        {
            Console.WriteLine("# NO FAILURES");
            return;
        }

        int index = 1;
        foreach (ValidationFailure failure in failures)
        {
            Console.WriteLine($"# FAILURE {index}");
            Console.WriteLine($"[{failure.GetType().Name}] {failure}");
            ++index;
        }
    }

    private static string GetWorkflowDefinition(string workflowName) =>
        typeof(Workflows).GetField(workflowName)?.GetValue(null) as string ??
        throw new InvalidOperationException($"Unknown workflow definition: {workflowName}");

    private static class Workflows
    {
        public const string EmptyWorkflow =
            """

            """;

        public const string OnlyComment =
            """
            # This is a comment
            """;

        public const string NotWorkflow =
            """
            users:
              - firstName: Alice
                lastName: Brown
                age: 61
                email: alice.brown@example.com
              - firstName: Alice
                lastName: Edwards
                age: 44
                email: alice.edwards@example.com
            """;

        public const string JsonExpression =
            """
            {
                "fistName": "Alice",
                "lastName": "Brown",
                "age": 61,
                "email": "alice.brown@example.com"
            }
            """;

        public const string InvalidYaml =
            """
            kind: AdaptiveDialog
            beginDialog:
              kind: OnActivity
              id: activity_xyz123
              type: Message
              actions:
                - kind: SetVariable
                  id: setVariable_u4cBtN
                  displayName: Invocation count
                  variable: Topic.Count
                  value: 0            
            - kind: SendActivity
                id: sendActivity_aGsbRo
                activity: Starting            
            """;

        public const string SimpleWorkflow =
            """
            kind: AdaptiveDialog
            beginDialog:
              kind: OnActivity
              id: activity_xyz123
              type: Message
              actions:
                - kind: SetVariable
                  id: setVariable_u4cBtN
                  displayName: Invocation count
                  variable: Topic.Count
                  value: 0

                - kind: SendActivity
                  id: sendActivity_aGsbRo
                  activity: Starting            
            """;
    }
}
