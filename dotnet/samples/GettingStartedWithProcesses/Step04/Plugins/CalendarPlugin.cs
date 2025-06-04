// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using System.Globalization;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel;

namespace Step04.Plugins;

internal sealed record CalendarEvent(
    string Title,
    string Start,
    string? End,
    string? Description = null)
{
    [JsonIgnore]
    public DateTime StartDate { get; } = DateTime.Parse(Start);

    [JsonIgnore]
    public DateTime? EndDate { get; } = End != null ? DateTime.Parse(End) : null;
}

/// <summary>
/// Mock plug-in to provide calendar information for the current and following month.
/// </summary>
/// <remarks>
/// Calendar information is simplified in the sense that any event covers the entire
/// day.  Also, no special treatment for weekend.
/// </remarks>
internal sealed class CalendarPlugin
{
    private static readonly DateTime s_now = DateTime.Now;
    private static readonly DateTime s_nextMonth = new(s_now.Year, DateTime.Now.AddMonths(1).Month, 1);

    private readonly List<CalendarEvent> _events = [];

    public CalendarPlugin()
    {
        CalendarGenerator generator = new();
        this._events =
            [
                .. generator.GenerateEvents(s_now.Month, s_now.Year),
                .. generator.GenerateEvents(s_nextMonth.Month, s_nextMonth.Year),
            ];
    }

    // Exposed for validation / no impact to plugin functionality
    public IReadOnlyList<CalendarEvent> Events => this._events;

    [KernelFunction]
    public string GetCurrentDate() => DateTime.Now.Date.ToString("dd-MMM-yyyy");

    [KernelFunction]
    [Description("Get the scheduled events that begin within the specified date range.")]
    public IReadOnlyList<CalendarEvent> GetEvents(
        [Description("The first date in the range")]
        string start,
        [Description("The final date in the range")]
        string end)
    {
        DateTime startDate = DateTime.Parse(start, CultureInfo.CurrentCulture);
        DateTime endDate = DateTime.Parse(end, CultureInfo.CurrentCulture);

        return this._events.Where(e => e.StartDate.Date >= startDate.Date && e.StartDate.Date < endDate.Date.AddDays(1)).ToArray();
    }

    [KernelFunction]
    [Description("Create a new scheduled event.")]
    public void NewEvent(string title, string startDate, string? endDate = null, string? description = null)
    {
        _events.Add(new CalendarEvent(title, startDate, endDate, description));
    }

    private sealed class CalendarGenerator
    {
        public int MaximumMultiDayEventCount => this._multiDayEvents.Count;

        public int MinimumEventGapInDays => 3; // Personal calendar less dense

        public IEnumerable<CalendarEvent> GenerateEvents(int month, int year)
        {
            int targetDayOfMonth = 1;
            do
            {
                bool isMultiDay = Random.Shared.Next(5) == 0 && this.MaximumMultiDayEventCount > 0;
                int daySpan = Random.Shared.Next(2, 8);
                int gapDays = Random.Shared.Next(this.MinimumEventGapInDays, 5);

                (string title, string description) = this.Pick(!isMultiDay);

                yield return new CalendarEvent(
                    title,
                    FormatDate(targetDayOfMonth),
                    isMultiDay ? FormatDate(targetDayOfMonth, daySpan) : null,
                    description);

                targetDayOfMonth += gapDays + 1 + (isMultiDay ? daySpan : 0);
            }
            while (targetDayOfMonth <= DateTime.DaysInMonth(year, month));

            string FormatDate(int day, int span = 0)
            {
                DateOnly date = new(year, month, day);
                date = date.AddDays(span);
                return date.ToString("dd-MMM-yyyy");
            }
        }

        private (string title, string description) Pick(bool isSingleDay)
        {
            return Pick(isSingleDay ? _singleDayEvents : _multiDayEvents);
        }

        private static (string title, string description) Pick(List<(string title, string description)> eventList)
        {
            int index = Random.Shared.Next(eventList.Count);
            try
            {
                return eventList[index];
            }
            finally
            {
                eventList.RemoveAt(index);
            }
        }

        public readonly List<(string title, string description)> _singleDayEvents =
            [
                ("Doctor's Appointment", "Annual physical check-up."),
                ("Grocery Shopping", "Weekly stock-up on essentials."),
                ("Yoga Class", "1-hour morning yoga session."),
                ("Car Maintenance", "Oil change and tire rotation."),
                ("Dinner with Friends", "Casual dinner at local restaurant."),
                ("Team Meeting", "Project update and discussion with the team."),
                ("Haircut Appointment", "Haircut and style at the salon."),
                ("Parent-Teacher Conference", "Discuss child's progress in school."),
                ("Dentist Appointment", "Teeth cleaning and routine check-up."),
                ("Workout Session", "Strength training at the gym."),
                ("Birthday Party", "Attending a friend's birthday celebration."),
                ("Movie Night", "Watch new release at the theater."),
                ("Volunteer Work", "Community cleanup event participation."),
                ("Job Interview", "Interview for potential new role."),
                ("Library Visit", "Return books and browse for new reads.")
            ];

        public readonly List<(string title, string description)> _multiDayEvents =
            [
                ("Vacation", "Relaxing trip with family."),
                ("Home Renovation Project", "Kitchen remodeling."),
                ("Annual Family Reunion", "Traveling to grandparents."),
            ];
    }
}
