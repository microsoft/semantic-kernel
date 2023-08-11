// Copyright (c) Microsoft. All rights reserved.

namespace PlayFabExamples.Example01_DataQnA.Reports;

public class DailyTopItemsReportRecord
{
    public static string GetHeader() => "ItemName,TotalSales,TotalRevenue";

    public string AsCsvRow() =>
        $"{this.ItemName.Replace("[\"", "").Replace("\"]", "")},{this.TotalSales},{this.TotalRevenue}";

    public static string GetDescription() =>
        """
        This dataset presents a thorough view of sales reports for a single day, capturing vital details about specific product performance and revenue generation.
        Each entry sheds light on sales figures per product, helping decision-makers enhance strategies for growth.
        The dataset is valuable for gauging product popularity, revenue trends, and customer engagement.
        The provided data empowers data-driven decision-making and supports efforts to enhance product offerings and optimize sales strategies for sustained success
        Description of Columns:
        - ItemName: The name of the product, representing a distinct item available for purchase.
        - TotalSales: The cumulative count of sales for the specific item, indicating its popularity and market demand.
        - TotalRevenue: The total monetary value of revenue generated from sales of the item in US dollars.
        """;

    public string ItemName { get; set; }
    public int TotalSales { get; set; }
    public decimal TotalRevenue { get; set; }
}
