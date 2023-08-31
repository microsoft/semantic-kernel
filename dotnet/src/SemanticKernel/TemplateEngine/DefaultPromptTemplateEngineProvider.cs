// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.TemplateEngine;

/// <summary>
/// Default implementation of <see cref = "IPromptTemplateEngine" /> which will be used with instances
/// of <see cref = "IKernel" /> if no alternate implementation is provided.
/// </summary>
public sealed class DefaultPromptTemplateEngineProvider : IPromptTemplateEngineProvider
{
    private static readonly DefaultPromptTemplateEngineProvider s_defaultPromptTemplateEngineFactory = new();

    private readonly Dictionary<string, IPromptTemplateEngineProvider> _factories = new();

    public const string DefaultFormat = "_DEFAULT_FORMAT_";

    private static bool _promptTemplateEngineInitialized = false;
    private static Type? _promptTemplateEngineType = null;

    /// <summary>
    /// Private constructor so there will only ever be one instance created.
    /// </summary>
    private DefaultPromptTemplateEngineProvider()
    {
        this.RegisterPromptTemplateEngineFactory(DefaultFormat, this.CreateDefaultPromptTemplateEngineFactory());
    }

    /// <summary>
    /// Singleton instance of <see cref = "DefaultPromptTemplateEngineProvider" />
    /// </summary>
    public static DefaultPromptTemplateEngineProvider Instance
    {
        get { return s_defaultPromptTemplateEngineFactory; }
    }

    /// <inheritdoc/>
    public IPromptTemplateEngine Create(string format, IKernel kernel, ILoggerFactory? loggerFactory = null)
    {
        if (this._factories.TryGetValue(format, out var factory))
        {
            return factory.Create(format, kernel, loggerFactory);
        }

        throw new InvalidOperationException($"No prompt template engine available to support the '{format}' format.");
    }

    /// <summary>
    /// Register a <see cref = "IPromptTemplateEngineProvider" /> instance which will be used
    /// to create <see cref = "IPromptTemplateEngine" />s for the specified format.
    /// </summary>
    /// <param name="format">Template format</param>
    /// <param name="factory"><see cref = "IPromptTemplateEngineProvider" /> instance</param>
    public void RegisterPromptTemplateEngineFactory(string format, IPromptTemplateEngineProvider factory)
    {
        if (string.IsNullOrEmpty(format))
        {
            throw new ArgumentException($"Invalid prompt template engine format, {format}.", nameof(format));
        }

        if (factory is null)
        {
            throw new ArgumentException("Prompt template engine must not be null.", nameof(factory));
        }

        if (this._factories.ContainsKey(format))
        {
            throw new InvalidOperationException($"Prompt template engine already registered for format, {format}.");
        }

        this._factories.Add(format, factory);
    }

    /// <summary>
    /// Create a default prompt template engine.
    ///
    /// This is a temporary solution to avoid breaking existing clients.
    /// There will be a separate task to add support for registering instances of IPromptTemplateEngine and obsoleting the current approach.
    ///
    /// </summary>
    /// <returns>Instance of <see cref="IPromptTemplateEngine"/>.</returns>
    private PromptTemplateEngineFactory CreateDefaultPromptTemplateEngineFactory()
    {
        if (!_promptTemplateEngineInitialized)
        {
            _promptTemplateEngineType = this.GetPromptTemplateEngineType();
            _promptTemplateEngineInitialized = true;
        }
        if (_promptTemplateEngineType is not null)
        {
            var constructor = _promptTemplateEngineType.GetConstructor(new Type[] { typeof(ILoggerFactory) });
            if (constructor is not null)
            {
                return new PromptTemplateEngineFactory(constructor);
            }
        }

        return new PromptTemplateEngineFactory(new NullPromptTemplateEngine());
    }
    /// <summary>
    /// Get the prompt template engine type if available
    /// </summary>
    /// <returns>The type for the prompt template engine if available</returns>
    private Type? GetPromptTemplateEngineType()
    {
        try
        {
            var assembly = Assembly.Load("Microsoft.SemanticKernel.TemplateEngine.PromptTemplateEngine");
            return assembly.ExportedTypes.Single(type =>
                type.Name.Equals("PromptTemplateEngine", StringComparison.Ordinal) &&
                type.GetInterface(nameof(IPromptTemplateEngine)) is not null);
        }
        catch (Exception ex) when (!ex.IsCriticalException())
        {
            return null;
        }
    }
}

/// <summary>
/// No-operation IPromptTemplateEngine which performs no rendering of the template.
///
/// This is a temporary solution to avoid breaking existing clients.
/// </summary>
internal class NullPromptTemplateEngine : IPromptTemplateEngine
{
    private readonly ILoggerFactory _loggerFactory;
    private readonly ILogger _logger;

    public NullPromptTemplateEngine(ILoggerFactory? loggerFactory = null)
    {
        this._loggerFactory = loggerFactory ?? NullLoggerFactory.Instance;
        this._logger = this._loggerFactory.CreateLogger(nameof(NullPromptTemplateEngine));
    }

    public Task<string> RenderAsync(string templateText, SKContext context, CancellationToken cancellationToken = default)
    {
        this._logger.LogTrace("Rendering string template: {0}", templateText);
        return Task.FromResult(templateText);
    }
}

/// <summary>
/// Implementation of IPromptTemplateEngineProvider which returns the provided instance of IPromptTemplateEngine.
/// </summary>
internal sealed class PromptTemplateEngineFactory : IPromptTemplateEngineProvider
{
    private ConstructorInfo? _constructor;
    private IPromptTemplateEngine? _engine;

    internal PromptTemplateEngineFactory(ConstructorInfo constructor)
    {
        if (constructor is null)
        {
            throw new ArgumentException("Prompt template engine constructor must not be null.", nameof(constructor));
        }

        this._constructor = constructor;
    }

    internal PromptTemplateEngineFactory(IPromptTemplateEngine engine)
    {
        if (engine is null)
        {
            throw new ArgumentException("Prompt template engine must not be null.", nameof(engine));
        }

        this._engine = engine;
    }

    public IPromptTemplateEngine Create(string format, IKernel kernel, ILoggerFactory? loggerFactory = null)
    {
        if (this._engine is not null)
        {
            return this._engine;
        }

        if (this._constructor is not null)
        {
#pragma warning disable CS8601 // Null logger factory is OK
            return (IPromptTemplateEngine)this._constructor.Invoke(new object[] { loggerFactory });
#pragma warning restore CS8601
        }

        throw new InvalidOperationException("Unable to create prompt template engine");
    }
}
