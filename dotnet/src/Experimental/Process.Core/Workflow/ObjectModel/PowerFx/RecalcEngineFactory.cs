// Copyright (c) Microsoft. All rights reserved.

using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class RecalcEngineFactory
{
    public static RecalcEngine Create(ProcessActionScopes scopes, int maximumExpressionLength)
    {
        RecalcEngine engine = new(CreateConfig());

        SetScope(ActionScopeTypes.Topic);
        SetScope(ActionScopeTypes.Global);
        SetScope(ActionScopeTypes.System);

        return engine;

        void SetScope(string scopeName)
        {
            RecordValue record = scopes[scopeName].BuildRecord();
            engine.UpdateVariable(scopeName, record);
        }

        PowerFxConfig CreateConfig()
        {
            PowerFxConfig config =
                new(Features.PowerFxV1)
                {
                    MaximumExpressionLength = maximumExpressionLength
                };

            config.EnableSetFunction();

            return config;
        }
    }
}
