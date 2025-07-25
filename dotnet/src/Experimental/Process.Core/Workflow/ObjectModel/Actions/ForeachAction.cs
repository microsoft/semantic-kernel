// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
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
        // %%% TODO: HACK: Assumes array
        this._index = 0;
        FormulaValue values = context.Engine.EvaluateExpression(this.Model.Items);
        TableValue tableValue = (TableValue)values;
        this._values = [.. tableValue.Rows.Select(row => row.Value.Fields.First().Value)];
        return Task.CompletedTask;
    }

    public void TakeNext(ProcessActionContext context)
    {
        if (this.HasValue = (this._index < this._values.Length))
        {
            FormulaValue value = this._values[this._index];
            this._index++;

            context.Engine.SetScopedVariable(context.Scopes, Throw.IfNull(this.Model.Value), value);

            if (this.Model.Index is not null)
            {
                context.Engine.SetScopedVariable(context.Scopes, this.Model.Index.Path, FormulaValue.New(this._index));
            }
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
