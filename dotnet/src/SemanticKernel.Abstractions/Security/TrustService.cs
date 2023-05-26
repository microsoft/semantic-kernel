// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Security;

/// <summary>
/// Default implementation of the trust service.
///
/// This is just a simple example implementation that will be used by default if no other is provided.
///
/// When set, throws an exception to stop execution when sensitive functions try to run with untrusted content.
/// </summary>
public sealed class TrustService : ITrustService
{
    /// <summary>
    /// Creates the default trusted implementation of the trust service.
    /// The default trusted version will use the trust information of the variables in the context to decide
    /// whether the result of the function call should be trusted or not.
    /// </summary>
    public static TrustService DefaultTrusted => new(true);

    /// <summary>
    /// Creates the default untrusted implementation of the trust service.
    /// The default untrusted version will always force the result of the function call to be untrusted.
    /// </summary>
    public static TrustService DefaultUntrusted => new(false);

    /// <summary>
    /// If set to:
    /// - false: will cause the context/prompt to always be considered untrusted, meaning the output of the function will always be considered untrusted.
    /// - true: will use the trust information of the variables in the context to decide whether the context/prompt is trusted or not
    /// (trusted only if all the variables within the context are trusted).
    /// </summary>
    private readonly bool _defaultTrusted;

    /// <inheritdoc/>
    public Task<bool> ValidateContextAsync(ISKFunction func, SKContext context)
    {
        return Task.FromResult(this.InternalValidation(func, context));
    }

    /// <inheritdoc/>
    public Task<TrustAwareString> ValidatePromptAsync(ISKFunction func, SKContext context, string prompt)
    {
        var isTrusted = this.InternalValidation(func, context);
        return Task.FromResult(new TrustAwareString(
            // This is only a sample implementation that directly returns the prompt
            prompt,
            // The content of the prompt will not be used in this example validation
            isTrusted: isTrusted
        ));
    }

    private TrustService(bool defaultTrusted)
    {
        this._defaultTrusted = defaultTrusted;
    }

    private bool InternalValidation(ISKFunction func, SKContext context)
    {
        bool contextIsTrusted = context.IsTrusted;
        if (func.IsSensitive && !contextIsTrusted)
        {
            throw new UntrustedContentException(
                UntrustedContentException.ErrorCodes.SensitiveFunctionWithUntrustedContent,
                $"Could not run {func.SkillName}.{func.Name}, the function is sensitive and the input untrusted"
            );
        }

        // If defaultTrusted == false, will always return false
        return contextIsTrusted && this._defaultTrusted;
    }
}
