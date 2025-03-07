// Copyright (c) Microsoft. All rights reserved.

using McpDotNet.Client;
using McpDotNet.Configuration;
using McpDotNet.Protocol.Types;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;

namespace ModelContextProtocol;

/// <summary>
/// Extension methods for McpDotNet
/// </summary>
internal static class McpDotNetExtensions
{
    /// <summary>
    /// Retrieve an <see cref="IMcpClient"/> instance configured to connect to a GitHub server running on stdio.
    /// </summary>
    internal static async Task<IMcpClient> GetGitHubToolsAsync()
    {
        McpClientOptions options = new()
        {
            ClientInfo = new() { Name = "GitHub", Version = "1.0.0" }
        };

        var config = new McpServerConfig
        {
            Id = "github",
            Name = "GitHub",
            TransportType = "stdio",
            TransportOptions = new Dictionary<string, string>
            {
                ["command"] = "npx",
                ["arguments"] = "-y @modelcontextprotocol/server-github",
            }
        };

        var factory = new McpClientFactory(
            [config],
            options,
            NullLoggerFactory.Instance
        );

        return await factory.GetClientAsync(config.Id).ConfigureAwait(false);
    }

    /// <summary>
    /// Map the tools exposed on this <see cref="IMcpClient"/> to a collection of <see cref="KernelFunction"/> instances for use with the Semantic Kernel.
    /// </summary>
    internal static async Task<IEnumerable<KernelFunction>> MapToFunctionsAsync(this IMcpClient mcpClient)
    {
        var tools = await mcpClient.ListToolsAsync().ConfigureAwait(false);
        return tools.Tools.Select(t => t.ToKernelFunction(mcpClient)).ToList();
    }

    #region private
    private static KernelFunction ToKernelFunction(this Tool tool, IMcpClient mcpClient)
    {
        async Task<string> InvokeToolAsync(Kernel kernel, KernelFunction function, KernelArguments arguments, CancellationToken cancellationToken)
        {
            try
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
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error invoking tool '{tool.Name}': {ex.Message}");

                // Rethrowing to allow the kernel to handle the exception
                throw;
            }
        }

        return KernelFunctionFactory.CreateFromMethod(
            method: InvokeToolAsync,
            functionName: tool.Name,
            description: tool.Description,
            parameters: tool.ToParameters(),
            returnParameter: ToReturnParameter()
        );
    }

    private static object ToArgumentValue(this KernelFunction function, string name, object value)
    {
        var parameter = function.Metadata.Parameters.FirstOrDefault(p => p.Name == name);
        return parameter?.ParameterType switch
        {
            Type t when Nullable.GetUnderlyingType(t) == typeof(int) => Convert.ToInt32(value),
            Type t when Nullable.GetUnderlyingType(t) == typeof(double) => Convert.ToDouble(value),
            Type t when Nullable.GetUnderlyingType(t) == typeof(bool) => Convert.ToBoolean(value),
            Type t when t == typeof(List<string>) => (value as IEnumerable<object>)?.ToList(),
            Type t when t == typeof(Dictionary<string, object>) => (value as Dictionary<string, object>)?.ToDictionary(kvp => kvp.Key, kvp => kvp.Value),
            _ => value,
        } ?? value;
    }

    private static List<KernelParameterMetadata>? ToParameters(this Tool tool)
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

    private static KernelReturnParameterMetadata? ToReturnParameter()
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
            "array" => typeof(List<string>),
            "object" => typeof(Dictionary<string, object>),
            _ => typeof(object)
        };

        return !required && type.IsValueType ? typeof(Nullable<>).MakeGenericType(type) : type;
    }
    #endregion
}
