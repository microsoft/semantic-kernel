// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning.ControlFlow;
public class StatementSkill
{
    private readonly IEnumerable<IStatementParser<Statement>> _supportedParsers;

    public StatementSkill(IEnumerable<IStatementParser<Statement>> supportedParsers)
    {
        this._supportedParsers = supportedParsers;
    }

    public Task<string> IfAsync(string ifContent, SKContext context)
    {
        // Only one parser per statement type should be added to the supported list.
        var parser = this._supportedParsers.OfType<IStatementParser<IfStatement>>().SingleOrDefault();

        if (parser is null)
        {
            throw new PlanningException(PlanningException.ErrorCodes.ParserNotFound, "If statement template parser not found");
        }

        IfStatement statement = parser.Parse(ifContent);
        if (statement.Evaluate(context))
        {
            return Task.FromResult(statement.ThenPlan);
        }
        return Task.FromResult(statement.ElsePlan ?? string.Empty);
    }
}
