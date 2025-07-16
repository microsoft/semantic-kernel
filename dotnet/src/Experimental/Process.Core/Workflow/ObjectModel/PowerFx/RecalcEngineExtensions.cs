// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class RecalcEngineExtensions
{
    public static void SetScopedVariable(this RecalcEngine engine, ProcessActionScopes scopes, string scopeName, string varName, FormulaValue value)
    {
        // Validate inputs and assign value.
        ProcessActionScope scope = scopes.AssignValue(scopeName, varName, value);

        // Rebuild scope record and update engine
        RecordValue scopeRecord = scope.BuildRecord();
        engine.DeleteFormula(scopeName);
        engine.UpdateVariable(scopeName, scopeRecord);
    }

    public static async Task ExecuteActionsAsync(this RecalcEngine engine, KernelProcessStepContext context, ProcessActionScopes scopes, ProcessAction action, Kernel kernel, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        try
        {
            // Execute each action in the current context
            //Console.WriteLine($"!!! ACTION {action.GetType().Name} [{action.Id}]"); // %%% DEVTRACE
            await action.HandleAsync(context, scopes, engine, kernel, cancellationToken).ConfigureAwait(false);
        }
        catch (ProcessActionException exception)
        {
            Console.WriteLine($"*** ACTION [{action.Id}] ERROR - {exception.GetType().Name}\n{exception.Message}"); // %%% DEVTRACE
            throw;
        }
        catch (Exception exception)
        {
            Console.WriteLine($"*** ACTION [{action.Id}] ERROR - {exception.GetType().Name}\n{exception.Message}"); // %%% DEVTRACE
            throw new ProcessActionException($"Unexpected failure executing action #{action.Id} [{action.GetType().Name}]", exception);
        }
    }

    public static FormulaValue EvaluateExpression(this RecalcEngine engine, ValueExpression? value)
    {
        if (value is null)
        {
            return BlankValue.NewBlank(); // %%% HANDLE NULL CASE
        }

        if (value.IsVariableReference)
        {
            return engine.Eval($"{value.VariableReference!.VariableScopeName}.{value.VariableReference!.VariableName}"); // %%% DRY
        }

        if (value.IsExpression)
        {
            return engine.Eval(value.ExpressionText);
        }

        if (value.IsLiteral)
        {
            DataValue? source = value.LiteralValue;
            return
                source switch
                {
                    null => FormulaValue.NewBlank(),
                    StringDataValue stringValue => FormulaValue.New(stringValue.Value),
                    NumberDataValue numberValue => FormulaValue.New(numberValue.Value),
                    BooleanDataValue boolValue => FormulaValue.New(boolValue.Value),
                    DateTimeDataValue dateTimeValue => FormulaValue.New(dateTimeValue.Value.DateTime),
                    DateDataValue dateValue => FormulaValue.New(dateValue.Value),
                    TimeDataValue timeValue => FormulaValue.New(timeValue.Value),
                    //RecordDataValue recordValue => FormulaValue.NewRecordFromFields(recordValue.Properties), // %%% TODO
                    //TableDataValue tableValue => FormulaValue.NewTable(), // %%% TODO
                    _ => FormulaValue.NewError(new Microsoft.PowerFx.ExpressionError { Message = $"Unknown literal type: {source.GetType().Name}" }),
                };
        }

        // %%% TODO: value.StructuredRecordExpression ???

        return BlankValue.NewBlank();
    }
}
