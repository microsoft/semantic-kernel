using System;
using System.Security;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace Microsoft.SemanticKernel.Security;

/// <summary>
/// Implements IFunctionInvocationFilter to provide a zero-allocation guardrail
/// against indirect prompt injection and tool hijacking attacks in multi-agent meshes.
/// </summary>
public sealed class BoundedExecutionFilter : IFunctionInvocationFilter
{
    private readonly BoundedExecutionEngine _besmEngine;
    private readonly int _currentStateId;
    
    public BoundedExecutionFilter(BoundedExecutionEngine engine, int currentStateId)
    {
        _besmEngine = engine;
        _currentStateId = currentStateId;
    }

    public async Task OnFunctionInvocationAsync(FunctionInvocationContext context, Func<FunctionInvocationContext, Task> next)
    {
        // For production, the target state ID and hash would be derived from context.Function
        // This is a reference implementation proving the intercept.
        int targetStateId = context.Function.Name.GetHashCode() & 0xFF; // Mock mapping
        ulong payloadHash = 1UL; // Mock hash for valid signature
        
        bool isTransitionValid = _besmEngine.ValidateTransition(_currentStateId, targetStateId, payloadHash);
        
        if (!isTransitionValid)
        {
            throw new SecurityException($"[BESM] Tool Hijacking Blocked: Unauthorized transition from agent state {_currentStateId} to tool state {targetStateId}.");
        }

        // Proceed with standard Semantic Kernel execution
        await next(context);
    }
}
