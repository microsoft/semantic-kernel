// Copyright (c) Microsoft. All rights reserved.

using Newtonsoft.Json.Linq;

namespace PlayFabExamples.Example01_DataQnA.Reports;
public class PlayFabReport
{
    /// <summary>
    /// Describes the report usage
    /// </summary>
    public required string Description { get; set; }
    public required IList<PlayFabReportColumn> Columns { get; set; }

    public required string CsvData { get; set; }
    public required string ReportName { get; set; }

    public string GetCsvHeader()
    {
        return string.Join(",", this.Columns.Select(c => c.Name));
    }

    public string GetDetailedDescription()
    {
        string columnsDescription =
            string.Join(
                Environment.NewLine,
                this.Columns.Select(column => $"- {column.Name}: {column.Description}"));
        string ret = $"{this.Description}{Environment.NewLine}Report columns: {Environment.NewLine}{columnsDescription}";
        return ret;
    }

    public static string CreateCsvReportFromJsonArray(string jsonArray, IList<PlayFabReportColumn> requiredProperties)
    {
        JArray jsonObjects = JArray.Parse(jsonArray);
        List<string> extractedProperties = new();

        foreach (JObject jsonObject in jsonObjects)
        {
            List<string> properties = new();

            foreach (PlayFabReportColumn property in requiredProperties)
            {
                string nameInSource = property.SourceName ?? property.Name;
                if (jsonObject.TryGetValue(nameInSource, out JToken value))
                {
                    string val = value.ToString();
                    val = property.SourceParser?.Invoke(val) ?? val;
                    properties.Add(val);
                }
                else
                {
                    properties.Add(""); // Empty value if property is missing
                }
            }

            extractedProperties.Add(string.Join(",", properties));
        }

        string ret = string.Join(Environment.NewLine, extractedProperties);
        return ret;
    }
}

public class PlayFabReportColumn
{
    public required string Name { get; set; }
    public required string Description { get; set; }
    public string? SourceName { get; internal set; }
    public Func<string, string>? SourceParser { get; set; }
}
