// Copyright (c) Microsoft. All rights reserved.

using McpDotNet.Client;
using McpDotNet.Configuration;
using McpDotNet.Protocol.Types;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;

namespace ModelContextProtocol;
internal static class McpClientUtils
{
    internal static async Task<IMcpClient> GetSimpleToolsAsync()
    {
        McpClientOptions options = new()
        {
            ClientInfo = new() { Name = "SimpleToolsConsole", Version = "1.0.0" }
        };

        var config = new McpServerConfig
        {
            Id = "everything",
            Name = "Everything",
            TransportType = "stdio",
            TransportOptions = new Dictionary<string, string>
            {
                ["command"] = "npx",
                ["arguments"] = "-y @modelcontextprotocol/server-everything",
            }
        };

        var factory = new McpClientFactory(
            [config],
            options,
            NullLoggerFactory.Instance
        );

        return await factory.GetClientAsync(config.Id).ConfigureAwait(false);
    }

    internal static async Task<IEnumerable<KernelFunction>> MapToFunctionsAsync(this IMcpClient mcpClient)
    {
        var tools = await mcpClient.ListToolsAsync().ConfigureAwait(false);
        return tools.Tools.Select(t => t.ToKernelFunction(mcpClient)).ToList();
    }

    internal static KernelFunction ToKernelFunction(this Tool tool, IMcpClient mcpClient)
    {
        async Task<string> InvokeToolAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            // Convert arguments to dictionary format expected by mcpdotnet
            Dictionary<string, object> mcpArguments = [];
            foreach (var arg in arguments)
            {
                if (arg.Value is not null)
                {
                    mcpArguments[arg.Key] = function.ToArgumentValue(arg.Key, arg.Value);
                }
            }

            // Call the tool through mcpdotnet
            var result = await mcpClient.CallToolAsync(
                tool.Name,
                mcpArguments,
                cancellationToken: cancellationToken
            ).ConfigureAwait(false);

            // Extract the text content from the result
            return string.Join("\n", result.Content
                .Where(c => c.Type == "text")
                .Select(c => c.Text));
        }

        return KernelFunctionFactory.CreateFromMethod(
            method: InvokeToolAsync,
            functionName: tool.Name,
            description: tool.Description,
            parameters: tool.ToParameters(),
            returnParameter: ToReturnParameter()
        );
    }

    internal static object ToArgumentValue(this KernelFunction function, string name, object value)
    {
        var parameter = function.Metadata.Parameters.FirstOrDefault(p => p.Name == name);
        return parameter?.ParameterType switch
        {
            Type t when t == typeof(int) => Convert.ToInt32(value),
            Type t when t == typeof(double) => Convert.ToDouble(value),
            Type t when t == typeof(bool) => Convert.ToBoolean(value),
            Type t when t == typeof(IEnumerable<object>) => (value as IEnumerable<object>)?.ToList(),
            Type t when t == typeof(IDictionary<string, object>) => (value as IDictionary<string, object>)?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value),
            _ => value,
        } ?? value;
    }

    internal static IEnumerable<KernelParameterMetadata>? ToParameters(this Tool tool)
    {
        var inputSchema = tool.InputSchema;
        var properties = inputSchema?.Properties;
        if (properties == null)
        {
            return null;
        }

        HashSet<string> requiredProperties = new(inputSchema!.Required ?? []);
        return properties.Select(kvp =>
            new KernelParameterMetadata(kvp.Key)
            {
                Description = kvp.Value.Description,
                ParameterType = ConvertParameterDataType(kvp.Value, requiredProperties.Contains(kvp.Key)),
                IsRequired = requiredProperties.Contains(kvp.Key)
            }).ToList();
    }

    internal static KernelReturnParameterMetadata? ToReturnParameter()
    {
        return new KernelReturnParameterMetadata()
        {
            ParameterType = typeof(string),
        };
    }
    private static Type ConvertParameterDataType(JsonSchemaProperty property, bool required)
    {
        var type = property.Type switch
        {
            "string" => typeof(string),
            "integer" => typeof(int),
            "number" => typeof(double),
            "boolean" => typeof(bool),
            "array" => typeof(IEnumerable<object>),
            "object" => typeof(IDictionary<string, object>),
            _ => typeof(object)
        };

        if (!required && type.IsValueType)
        {
            return typeof(Nullable<>).MakeGenericType(type);
        }

        return type;
    }
}
