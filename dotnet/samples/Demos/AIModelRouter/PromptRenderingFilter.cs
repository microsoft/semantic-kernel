// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;

#pragma warning disable SKEXP0001
#pragma warning disable SKEXP0010
#pragma warning disable CA2249 // Consider using 'string.Contains' instead of 'string.IndexOf'

namespace AIModelRouter;

internal partial class Program
{
    /// <summary>
    /// Using a filter to log the service being used for the prompt.
    /// </summary>
    public class PromptRenderingFilter : IPromptRenderFilter
    {
        public Task OnPromptRenderAsync(PromptRenderContext context, Func<PromptRenderContext, Task> next)
        {
            Console.ForegroundColor = ConsoleColor.Yellow;
            Console.WriteLine($"Selected service id: '{context.Arguments.ExecutionSettings?.FirstOrDefault().Key}'");
            Console.ForegroundColor = ConsoleColor.White;
            return next(context);
        }
    }
}
