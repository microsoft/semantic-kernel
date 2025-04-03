// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;
using System;
using MCPServer.Resources;
using Microsoft.SemanticKernel;
using ModelContextProtocol.Protocol.Types;
using ModelContextProtocol.Server;
using HandlebarsDotNet;
using Microsoft.Extensions.DependencyInjection.Extensions;
using MCPServer.Prompts;
using Microsoft.Extensions.DependencyInjection;
using System.Diagnostics;

namespace MCPServer;

/// <summary>
/// Extension methods for <see cref="IMcpServerBuilder"/>.
/// </summary>
public static class McpServerBuilderExtensions
{
    /// <summary>
    /// Adds all functions of the kernel plugins as tools to the server.
    /// </summary>
    /// <param name="builder">The builder instance.</param>
    /// <param name="plugins">The kernel plugins to add as tools to the server.</param>
    /// <returns>The builder instance.</returns>
    public static IMcpServerBuilder WithTools(this IMcpServerBuilder builder, KernelPluginCollection plugins)
    {
        foreach (var plugin in plugins)
        {
            foreach (var function in plugin)
            {
                builder.Services.AddSingleton(services => McpServerTool.Create(function.AsAIFunction()));
            }
        }

        return builder;
    }

    public static IMcpServerBuilder AddResourceTemplate(
        this IMcpServerBuilder builder,
        ResourceTemplate template,
        Func<RequestContext<ReadResourceRequestParams>, IServiceProvider, IDictionary<string, string>, CancellationToken, Task<ReadResourceResult>> handler)
    {
        builder.WithListResourceTemplatesHandler()

        builder.Services.AddSingleton((Func<IServiceProvider, ResourceTemplateDefinition>)(
            services =>
            {
                Debugger.Break();

                string pattern = "^" +
                             Regex.Escape(template.UriTemplate)
                            .Replace("\\{", "(?<")
                            .Replace("}", @">[^/]+)") + "$";

                Regex regex = new(pattern);

                var templateDefinition = new ResourceTemplateDefinition
                {
                    ResourceTemplate = template,
                    IsMatch = (uri) => regex.IsMatch(uri),
                    Handler = async (context, cancellationToken) =>
                    {
                        Match match = regex.Match(context.Params!.Uri!);

                        if (!match.Success)
                        {
                            throw new ArgumentException($"The uri '{context.Params.Uri}' does not match the template '{template.UriTemplate}'.");
                        }

                        var arguments = match.Groups.Cast<Group>()
                                .Where(g => g.Success && g.Name != "0")
                                .ToDictionary(g => g.Name, g => g.Value);

                        return await handler(context, services, arguments, cancellationToken);
                    },
                };

                var handlers = services.GetRequiredService<McpServerHandlers>();
                if (handlers.ListResourceTemplatesHandler is null || handlers.ReadResourceHandler is null)
                {
                    var registry = new ResourceRegistryDI(services.GetServices<ResourceTemplateDefinition>().ToList());

                    handlers.ListResourceTemplatesHandler = registry.HandleListResourceTemplatesRequestAsync;
                    handlers.ReadResourceHandler = registry.HandleReadResourceRequestAsync;
                }

                return templateDefinition;
            }
        ));

        //if (!builder.Services.Any(x => x.ServiceType == typeof(ResourceRegistryDI)))
        //{
        //    builder.Services.AddSingleton<ResourceRegistryDI>(s =>
        //    {
        //        Debugger.Break();
        //        var resourceTemplateDefinitions = s.GetServices<ResourceTemplateDefinition>().ToList();

        //        var registry = new ResourceRegistryDI(resourceTemplateDefinitions);

        //        var handlers = s.GetRequiredService<McpServerHandlers>();
        //        handlers.ListResourceTemplatesHandler = registry.HandleListResourceTemplatesRequestAsync;
        //        handlers.ReadResourceHandler = registry.HandleReadResourceRequestAsync;

        //        return registry;
        //    });
        //}

        //builder.Services.AddSingleton<ResourceRegistryDI>();

        //builder.Services.AddSingleton((Func<IServiceProvider, McpServerTool>)(services => null!));

        //builder.Services.Configure<McpServerHandlers>(s => s.ListResourceTemplatesHandler = handler);

        //builder.Services.Configure<McpServerOptions>(options =>
        //{
        //    options.ResourceTemplates.Add(new ResourceTemplateDefinition
        //    {
        //        ResourceTemplate = template,
        //        Handler = async (context, cancellationToken) =>
        //        {
        //            var result = await handler(context, context.Params.Arguments, cancellationToken);
        //            return result;
        //        }
        //    });
        //});

        //services.AddSingleton<MCPServer>();
        //services.AddSingleton<MCPServerService>();

        return builder;
    }

    public static IMcpServerBuilder AddResourceTemplate1(
        this IMcpServerBuilder builder,
        ResourceTemplate template,
        Func<RequestContext<ReadResourceRequestParams>, IServiceProvider, IDictionary<string, string>, CancellationToken, Task<ReadResourceResult>> handler)
    {
        builder.Services.AddSingleton((Func<IServiceProvider, ResourceTemplateDefinition>)(
            services =>
            {
                Debugger.Break();

                string pattern = "^" +
                             Regex.Escape(template.UriTemplate)
                            .Replace("\\{", "(?<")
                            .Replace("}", @">[^/]+)") + "$";

                Regex regex = new(pattern);

                var templateDefinition = new ResourceTemplateDefinition
                {
                    ResourceTemplate = template,
                    IsMatch = (uri) => regex.IsMatch(uri),
                    Handler = async (context, cancellationToken) =>
                    {
                        Match match = regex.Match(context.Params!.Uri!);

                        if (!match.Success)
                        {
                            throw new ArgumentException($"The uri '{context.Params.Uri}' does not match the template '{template.UriTemplate}'.");
                        }

                        var arguments = match.Groups.Cast<Group>()
                                .Where(g => g.Success && g.Name != "0")
                                .ToDictionary(g => g.Name, g => g.Value);

                        return await handler(context, services, arguments, cancellationToken);
                    },
                };

                var handlers = services.GetRequiredService<McpServerHandlers>();
                if (handlers.ListResourceTemplatesHandler is null || handlers.ReadResourceHandler is null)
                {
                    var registry = new ResourceRegistryDI(services.GetServices<ResourceTemplateDefinition>().ToList());

                    handlers.ListResourceTemplatesHandler = registry.HandleListResourceTemplatesRequestAsync;
                    handlers.ReadResourceHandler = registry.HandleReadResourceRequestAsync;
                }

                return templateDefinition;
            }
        ));

        //if (!builder.Services.Any(x => x.ServiceType == typeof(ResourceRegistryDI)))
        //{
        //    builder.Services.AddSingleton<ResourceRegistryDI>(s =>
        //    {
        //        Debugger.Break();
        //        var resourceTemplateDefinitions = s.GetServices<ResourceTemplateDefinition>().ToList();

        //        var registry = new ResourceRegistryDI(resourceTemplateDefinitions);

        //        var handlers = s.GetRequiredService<McpServerHandlers>();
        //        handlers.ListResourceTemplatesHandler = registry.HandleListResourceTemplatesRequestAsync;
        //        handlers.ReadResourceHandler = registry.HandleReadResourceRequestAsync;

        //        return registry;
        //    });
        //}

        //builder.Services.AddSingleton<ResourceRegistryDI>();

        //builder.Services.AddSingleton((Func<IServiceProvider, McpServerTool>)(services => null!));

        //builder.Services.Configure<McpServerHandlers>(s => s.ListResourceTemplatesHandler = handler);

        //builder.Services.Configure<McpServerOptions>(options =>
        //{
        //    options.ResourceTemplates.Add(new ResourceTemplateDefinition
        //    {
        //        ResourceTemplate = template,
        //        Handler = async (context, cancellationToken) =>
        //        {
        //            var result = await handler(context, context.Params.Arguments, cancellationToken);
        //            return result;
        //        }
        //    });
        //});

        //services.AddSingleton<MCPServer>();
        //services.AddSingleton<MCPServerService>();

        return builder;
    }
}
