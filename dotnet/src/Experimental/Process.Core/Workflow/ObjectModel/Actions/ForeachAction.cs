// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Abstractions;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ForeachAction : ProcessAction<Foreach>
{
    private int _index;
    private FormulaValue[] _values;

    public ForeachAction(Foreach model)
        : base(model)
    {
        this._values = [];
    }

    public bool HasValue { get; private set; }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        this._index = 0;

        if (this.Model.Items is null)
        {
            this._values = [];
            this.HasValue = false;
            return Task.CompletedTask;
        }

        EvaluationResult<DataValue> result = context.ExpressionEngine.GetValue(this.Model.Items, context.Scopes);
        TableDataValue tableValue = (TableDataValue)result.Value; // %%% CAST - TYPE ASSUMPTION (TableDataValue)
        this._values = [.. tableValue.Values.Select(value => value.Properties.Values.First().ToFormulaValue())];
        return Task.CompletedTask;
    }

    public void TakeNext(ProcessActionContext context)
    {
        if (this.HasValue = (this._index < this._values.Length))
        {
            FormulaValue value = this._values[this._index];

            context.Engine.SetScopedVariable(context.Scopes, Throw.IfNull(this.Model.Value), value);

            if (this.Model.Index is not null)
            {
                context.Engine.SetScopedVariable(context.Scopes, this.Model.Index.Path, FormulaValue.New(this._index));
            }

            this._index++;
        }
    }

    public void Reset(ProcessActionContext context)
    {
        context.Engine.ClearScopedVariable(context.Scopes, Throw.IfNull(this.Model.Value));
        if (this.Model.Index is not null)
        {
            context.Engine.ClearScopedVariable(context.Scopes, this.Model.Index);
        }
    }
}
