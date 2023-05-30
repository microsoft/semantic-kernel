// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Security;

/// <summary>
/// Base interface used to handle trust events and validation. The flow in the SKFunction is:
///
/// - Semantic function
///     - Call ValidateContextAsync
///     - Render prompt using template and variables
///     - Call ValidatePromptAsync with rendered template and context
///     - Call completion client with the returned prompt from ValidatePromptAsync
///     - Update result
///
/// - Native function
///     - Call ValidateContextAsync
///     - Call native function implementation
///     - Update result
/// </summary>
public interface ITrustService
{
    /// <summary>
    /// Called by the SKFunction flow to validate if the current context is considered to be trusted or not:
    ///
    /// - This is called for semantic functions before rendering the prompt template.
    /// - This is called for native functions before calling the native function implementation.
    ///
    /// If the return is false, this means the result of the function will be tagged as untrusted.
    ///
    /// The implementation might depend on the application needs. A simple sample implementation
    /// could be accomplished by analyzing the variables in the context, if they are all trusted, then
    /// consider the context to be trusted.
    ///
    /// This also gives an opportunity for the context to be updated or actions to be taken if
    /// potentially untrusted content is found. For example, sanitizing an untrusted variable and turning it into trusted.
    /// </summary>
    /// <param name="func">Instance of the function being called</param>
    /// <param name="context">The current execution context</param>
    /// <returns>Should return whether the result of the function should be considered trusted depending on the context</returns>
    Task<bool> ValidateContextAsync(ISKFunction func, SKContext context);

    /// <summary>
    /// This will only be called by semantic functions. It will be called in the SKFunction flow after the prompt is
    /// rendered using the given template, and before calling the text completion with the rendered prompt.
    ///
    /// It should return the content to be used in the completion client as a TrustAwareString, which will include
    /// trust information. If the TrustAwareString returned is not trusted, this means the result of the function will be tagged as untrusted.
    ///
    /// After the template is rendered, the context might be tagged as untrusted because the template might contain function calls
    /// that turned the context into untrusted when rendered.
    ///
    /// The implementation might depend on the application needs. A simple sample implementation
    /// could be accomplished by analyzing the variables in the context and the rendered prompt, if everything is trusted, then
    /// return the prompt wrapped in a TrustAwareString and tagged as trusted.
    ///
    /// This also gives an opportunity for both the context and the prompt to be updated before calling the completion client
    /// when something untrusted is identified. For example, sanitizing an untrusted prompt and turning it into trusted.
    /// </summary>
    /// <param name="func">Instance of the function being called</param>
    /// <param name="context">The current execution context</param>
    /// <param name="prompt">The current rendered prompt to be used with the completion client</param>
    /// <returns>Should return a TrustAwareString representing the final prompt to be used for the completion client.
    /// The TrustAwareString includes trust information</returns>
    Task<TrustAwareString> ValidatePromptAsync(ISKFunction func, SKContext context, string prompt);
}
