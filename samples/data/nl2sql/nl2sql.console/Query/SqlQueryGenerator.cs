// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Query;

using System;
using System.Linq;
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

    public async Task<(string?, string?)> SolveObjectiveAsync(string objective, SKContext context)
    {
        var schemaName = this.schemaProvider.Schemas.SingleOrDefault().Item1; // $$$ BROKE
        var schemaText = await this.schemaProvider.GetSchemaAsync(schemaName).ConfigureAwait(false);

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
            return (null, null);
        }

        return (schemaName, context.GetResult(ContextLabelQuery, require: false));
    }
}
