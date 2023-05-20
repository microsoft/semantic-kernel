// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using SemanticKernel.Service.Auth;
using SemanticKernel.Service.Models;

namespace SemanticKernel.Service.Utilities;

public class AskConverter
{
    private readonly IAuthInfo _authInfo;

    public AskConverter(IAuthInfo authInfo)
    {
        this._authInfo = authInfo;
    }

    /// <summary>
    /// Converts <see cref="Ask"/> variables to <see cref="ContextVariables"/>, inserting some system variables along the way.
    /// </summary>
    public ContextVariables GetContextVariables(Ask ask)
    {
        const string userIdKey = "userId";
        const string userNameKey = "userName";
        var contextVariables = new ContextVariables(ask.Input);
        foreach (var input in ask.Variables)
        {
            if (input.Key == userIdKey)
            {
                contextVariables.Set(userIdKey, this._authInfo.UserId);
            }
            else if (input.Key == userNameKey)
            {
                contextVariables.Set(userNameKey, this._authInfo.Name);
            }
            else
            {
                contextVariables.Set(input.Key, input.Value);
            }
        }

        return contextVariables;
    }
}
