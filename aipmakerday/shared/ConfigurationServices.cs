namespace SemanticKernel.HelloAgents.Internal;

using Microsoft.Extensions.Configuration;

internal static class ConfigurationServices
{
    private static IConfigurationRoot? configuration;

    public static IConfigurationRoot GetConfiguration() =>
        configuration ??=
            new ConfigurationBuilder()
                .AddEnvironmentVariables()
                .AddJsonFile("settings.json", optional: true)
                .AddJsonFile("settings.development.json", optional: true)
                .AddUserSecrets<Program>(optional: true)
                .Build();

    public static FoundrySettings GetFoundrySettings()
    {
        IConfigurationRoot configuration = GetConfiguration();

        FoundrySettings settings = GetSettings<FoundrySettings>(FoundrySettings.Section);

        settings.ConnectionString = configuration[FoundrySettings.ConnectionStringSetting] ?? string.Empty;

        return settings;
    }

    public static TSettings GetSettings<TSettings>(string section) =>
        GetConfiguration().GetRequiredSection(section).Get<TSettings>() ??
        throw new InvalidOperationException($"Undefined settings section: {section}");
}
