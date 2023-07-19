// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library;

using System;
using System.ComponentModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using SemanticKernel.Data.Nl2Sql.Library.Internal;
using SemanticKernel.Data.Nl2Sql.Library.Schema;

/// <summary>
/// Generate SQL query targeting Microsoft SQL Server.
/// </summary>
public sealed class SqlQueryGenerator
{
    public const string ContextParamObjective = "data_objective";
    public const string ContextParamSchema = "data_schema";
    public const string ContextParamSchemaId = "data_schema_id";

    private const string ContentLabelQuery = "sql";
    private const string ContentLabelAnswer = "answer";
    private const string ContentAffirmative = "yes";

    private const string SkillName = "nl2sql";

    private readonly ISKFunction promptEval;
    private readonly ISKFunction promptGenerator;

    public SqlQueryGenerator(IKernel kernel, string rootSkillFolder)
    {
        var functions = kernel.ImportSemanticSkillFromDirectory(rootSkillFolder, SkillName);
        this.promptEval = functions["isquery"];
        this.promptGenerator = functions["generatequery"];

        kernel.ImportSkill(this, SkillName);
    }

    /// <summary>
    /// Attempt to produce a query for the given objective based on the registerted schemas.
    /// </summary>
    /// <param name="objective">A natural language objective</param>
    /// <param name="context">A <see cref="SKContext"/> object</param>
    /// <returns>A SQL query (or null if not able)</returns>
    [SKFunction, Description("Generate a data query for a given objective and schema")]
    [SKName("GenerateQueryFromObjective")]
    public async Task<string?> SolveObjectiveAsync(string objective, SKContext context)
    {
        // Search for schema with best similiarity match to the objective
        var recall =
            await context.Memory.SearchAsync(
                SchemaProvider.MemoryCollectionName,
                objective,
                limit: 1,
                minRelevanceScore: 0.75,
                withEmbeddings: true).ToArrayAsync().ConfigureAwait(false);

        var best = recall.FirstOrDefault();
        if (best == null)
        {
            return null; // No schema / no query
        }

        var schemaName = best.Metadata.Id;
        var schemaText = best.Metadata.Text;

        context[ContextParamObjective] = objective;
        context[ContextParamSchema] = schemaText;
        context[ContextParamSchemaId] = schemaName;

        // Screen objective to determine if it can be solved with the selected schema.
        if (!await this.ScreenObjectiveAsync(context).ConfigureAwait(false))
        {
            return null; // Objective doesn't pass screen
        }

        // Generate query
        await this.promptGenerator.InvokeAsync(context).ConfigureAwait(false);

        // Parse result to handle 
        return context.GetResult(ContentLabelQuery);
    }

    private async Task<bool> ScreenObjectiveAsync(SKContext context)
    {
        await this.promptEval.InvokeAsync(context).ConfigureAwait(false);

        var answer = context.GetResult(ContentLabelAnswer);

        return answer.Equals(ContentAffirmative, StringComparison.OrdinalIgnoreCase);
    }
}
