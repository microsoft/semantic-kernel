// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Query;

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Data.Nl2Sql.Services;

/// <summary>
/// Generate SQL query targeting Microsoft SQL Server.
/// </summary>
internal sealed class SqlQueryGenerator
{
    public const string ContextParamObjective = "objective";
    public const string ContextParamSchema = "schema";
    public const string ContextLabelAnswer = "answer";
    public const string ContextLabelQuery = "sql";
    public const string ContentAffirmative = "yes";

    private readonly ISKFunction promptEval;
    private readonly ISKFunction promptGenerator;
    private readonly SchemaProvider schemaProvider;

    public SqlQueryGenerator(IKernel kernel, SchemaProvider schemaProvider)
    {
        this.schemaProvider = schemaProvider;

        var functions = kernel.ImportSemanticSkillFromDirectory(Program.ConfigRoot, "nl2sql");
        this.promptEval = functions["isquery"];
        this.promptGenerator = functions["generatequery"];
    }

    public async Task<string?> SolveObjectiveAsync(string objective, string? schemaText, SKContext context)
    {
        if (string.IsNullOrEmpty(schemaText))
        {
            return null;
        }

        context[ContextParamObjective] = objective;
        context[ContextParamSchema] = schemaText;

        await this.promptEval.InvokeAsync(context).ConfigureAwait(false);

        var answer = context.GetResult(ContextLabelAnswer, require: false);
        if (answer.Equals(ContentAffirmative, StringComparison.OrdinalIgnoreCase))
        {
            await this.promptGenerator.InvokeAsync(context).ConfigureAwait(false);
        }
        else
        {
            context.Fail("The objective does not correspond to a data query associated with this schema.");
            return null;
        }

        return context.GetResult(ContextLabelQuery, require: false);
    }
}
