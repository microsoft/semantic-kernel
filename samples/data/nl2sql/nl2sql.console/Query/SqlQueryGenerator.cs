// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Query;

using System;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Generate SQL query targeting Microsoft SQL Server.
/// </summary>
internal sealed class SqlQueryGenerator
{
    public const string ContextParamObjective = "data_objective";
    public const string ContextParamSchema = "data_schema";
    public const string ContextParamSchemaId = "data_schema_id";

    private const string ContentLabelQuery = "sql";
    private const string ContentLabelAnswer = "answer";
    private const string ContentAffirmative = "yes";

    private readonly ISKFunction promptEval;
    private readonly ISKFunction promptGenerator;

    public SqlQueryGenerator(IKernel kernel)
    {
        var functions = kernel.ImportSemanticSkillFromDirectory(Repo.RootConfig, "nl2sql");
        this.promptEval = functions["isquery"];
        this.promptGenerator = functions["generatequery"];

        kernel.ImportSkill(this, "nl2sql");
    }

    [SKFunction, Description("Generate a data query for a given objective and schema")]
    [SKName("GenerateQueryFromObjective")]
    public async Task<string?> SolveObjectiveAsync(string objective, SKContext context)
    {
        var recall =
            await context.Memory.SearchAsync(
                "schemas",
                objective,
                limit: 1,
                minRelevanceScore: 0.75,
                withEmbeddings: true).ToArrayAsync().ConfigureAwait(false);

        var best = recall.FirstOrDefault();
        if (best == null)
        {
            return null;
        }

        var schemaName = best.Metadata.Id;
        var schemaText = best.Metadata.Text;

        context[ContextParamObjective] = objective;
        context[ContextParamSchema] = schemaText;
        context[ContextParamSchemaId] = schemaName;

        if (!await this.ScreenObjectiveAsync(context).ConfigureAwait(false))
        {
            return null; // Objective doesn't pass screen
        }

        // Generate query
        await this.promptGenerator.InvokeAsync(context).ConfigureAwait(false);

        return context.GetResult(ContentLabelQuery, require: false);
    }

    private async Task<bool> ScreenObjectiveAsync(SKContext context)
    {
        await this.promptEval.InvokeAsync(context).ConfigureAwait(false);

        var answer = context.GetResult(ContentLabelAnswer, require: false);

        return answer.Equals(ContentAffirmative, StringComparison.OrdinalIgnoreCase);
    }
}
