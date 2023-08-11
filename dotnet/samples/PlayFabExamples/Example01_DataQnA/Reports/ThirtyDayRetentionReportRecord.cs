// Copyright (c) Microsoft. All rights reserved.

using Newtonsoft.Json;

namespace PlayFabExamples.Example01_DataQnA.Reports;

public class ThirtyDayRetentionReportRecord
{
    public static string GetHeader() => "CohortDate,CohortSize,DaysLater,TotalRetained,PercentRetained";

    public string AsCsvRow() =>
        $"{this.CohortDate:yyyy/MM/dd},{this.CohortSize},{this.DaysLater},{this.TotalRetained},{this.PercentRetained}";

    public static string GetDescription() =>
        """
        The provided CSV table contains retention report for daily cohorts of players in the last 30 days.
        This retention dataset helps analyze player engagement and the effectiveness of retention strategies by tracking player behavior over time periods.
        It can offer insights into player retention rates, allowing game developers to make informed decisions to improve player engagement and overall game experience.
        Below is the description of each field in the table:
        - CohortDate: The timestamp indicating when the retention data was collected
        - CohortSize: The initial size of the cohort, representing the number of players at the beginning of the retention period.
        - DaysLater: The number of days later at which the retention is being measured.
        - TotalRetained: The total number of players retained in the specified cohort after the specified number of days.
        - PercentRetained: The percentage of players retained in the cohort after the specified number of days.
        """;

    [JsonProperty("Ts")]
    public DateTime CohortDate { get; set; }
    public int CohortSize { get; set; }
    [JsonProperty("PeriodsLater")]
    public int DaysLater { get; set; }
    public int TotalRetained { get; set; }
    public double PercentRetained { get; set; }
}
