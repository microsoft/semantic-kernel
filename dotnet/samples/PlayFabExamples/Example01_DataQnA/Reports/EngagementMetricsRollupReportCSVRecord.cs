// Copyright (c) Microsoft. All rights reserved.

namespace PlayFabExamples.Example01_DataQnA.Reports;

public class EngagementMetricsRollupReportCSVRecord
{
    public static string GetHeader() => "Date,Region,MonthlyActiveUsers,DailyActiveUsers,NewPlayers,Retention1Day,Retention7Day";

    public string AsCsvRow() =>
        $"{this.ReportDate:yyyy/MM/dd},{this.Region},{this.MonthlyActiveUsers},{this.DailyActiveUsers},{this.NewPlayers},{this.Retention1Day},{this.Retention7Day}";

    public static string GetDescription() =>
        """
        The provided CSV table contains weekly aggregated data related to the user activity and retention for a gaming application.
        This data is broken down by different geographic regions, including France, Greater China, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe.
        Each row represents a different geographic regions, and the columns contain specific metrics related to user engagement.
        There is a special row for each week with the Region set to 'All', which means this row aggregates data across all the regions for that week
        Below is the description of each field in the table:
        - ReportDate: The date for week for which the data is recorded
        - Region: The geographic region to which the data pertains.Examples include Greater China, France, Japan, United Kingdom, United States, Latin America, India, Middle East & Africa, Germany, Canada, Western Europe, Asia Pacific, and Central & Eastern Europe.
        - MonthlyActiveUsers: The total number of unique users who engaged with the game at least once during the month
        - DailyActiveUsers: The total number of unique users who engaged with the game on that week.
        - NewPlayers: The number of new users who joined and engaged with the game on that week.
        - Retention1Day: The percentage of users who returned to the game on the day after their first engagement.
        - Retention7Day: The percentage of users who returned to the game seven days after their first engagement.
        """;

    public DateTime ReportDate { get; set; }
    public string Platform { get; set; }
    public string Region { get; set; }
    public string Segment { get; set; }
    public long MonthlyActiveUsers { get; set; }
    public long DailyActiveUsers { get; set; }
    public long NewPlayers { get; set; }
    public double FocusAverageDuration { get; set; }
    public double FocusAveragePeriodsPerUser { get; set; }
    public long FocusTotalPeriods { get; set; }
    public double Retention1Day { get; set; }
    public double Retention7Day { get; set; }
    public double Retention14Day { get; set; }
    public double Retention30Day { get; set; }
    public double RevenueDollars { get; set; }
}
