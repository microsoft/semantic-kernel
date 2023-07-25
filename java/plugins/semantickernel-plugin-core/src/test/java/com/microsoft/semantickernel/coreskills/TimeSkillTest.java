// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Locale;

@SuppressWarnings("ReturnValueIgnored")
public class TimeSkillTest {

    private static final String defaultLocale = "en-US";

    private static final ZonedDateTime mockDateTime;

    static {
        mockDateTime = ZonedDateTime.of(2025, 1, 12, 9, 15, 7, 0, ZoneId.systemDefault());
    }

    private TimeSkill timeSkill;

    @BeforeEach
    public void setUp() {
        timeSkill = spy(new TimeSkill());
        when(timeSkill.now()).thenReturn(mockDateTime);
    }

    @Test
    public void testDate() {
        String result = timeSkill.date(defaultLocale);
        assertEquals("Sunday, January 12, 2025", result);
    }

    @Test
    public void testTime() {
        String result = timeSkill.time(defaultLocale);
        assertEqualsIgnoreCase("09:15:07 AM", result);
    }

    @Test
    public void testToday() {
        String result = timeSkill.today(defaultLocale);
        assertEquals("Sunday, January 12, 2025", result);
    }

    @Test
    public void testNow() {
        String result = timeSkill.now(defaultLocale);
        assertEqualsIgnoreCase("Sunday, January 12, 2025 9:15 AM", result);
    }

    @Test
    public void testYear() {
        String result = timeSkill.year(defaultLocale);
        assertEquals("2025", result);
    }

    @Test
    public void testMonth() {
        String result = timeSkill.month(defaultLocale);
        assertEquals("January", result);
    }

    @Test
    public void testMonthNumber() {
        String result = timeSkill.monthNumber(defaultLocale);
        assertEquals("01", result);
    }

    @Test
    public void testDay() {
        String result = timeSkill.day(defaultLocale);
        assertEquals("12", result);
    }

    @Test
    public void testDayOfWeek() {
        String result = timeSkill.dayOfWeek(defaultLocale);
        assertEquals("Sunday", result);
    }

    @Test
    public void testHour() {
        String result = timeSkill.hour(defaultLocale);
        assertEqualsIgnoreCase("9 AM", result);
    }

    @Test
    public void testHourNumber() {
        String result = timeSkill.hourNumber(defaultLocale);
        assertEquals("09", result);
    }

    @Test
    public void testMinute() {
        String result = timeSkill.minute(defaultLocale);
        assertEquals("15", result);
    }

    @Test
    public void testSecond() {
        String result = timeSkill.second(defaultLocale);
        assertEquals("07", result);
    }

    @Test
    public void daysAgo() {
        assertEquals("Thursday, January 9, 2025", timeSkill.daysAgo("3", defaultLocale));
        assertEquals("Tuesday, January 7, 2025", timeSkill.daysAgo("5", defaultLocale));
    }

    @Test
    public void testDateMatchingLastDayName() {
        assertEquals(
                "Sunday, January 5, 2025",
                timeSkill.dateMatchingLastDayName("Sunday", defaultLocale));
        assertEquals(
                "Monday, January 6, 2025",
                timeSkill.dateMatchingLastDayName("Monday", defaultLocale));
        assertEquals(
                "Tuesday, January 7, 2025",
                timeSkill.dateMatchingLastDayName("Tuesday", defaultLocale));
        assertEquals(
                "Wednesday, January 8, 2025",
                timeSkill.dateMatchingLastDayName("wednesday", defaultLocale));
        assertEquals(
                "Thursday, January 9, 2025",
                timeSkill.dateMatchingLastDayName("thursday", defaultLocale));
        assertEquals(
                "Friday, January 10, 2025",
                timeSkill.dateMatchingLastDayName("Friday", defaultLocale));
        assertEquals(
                "Saturday, January 11, 2025",
                timeSkill.dateMatchingLastDayName("Saturday", defaultLocale));
    }

    public void assertEqualsIgnoreCase(String a, String b) {
        Assertions.assertEquals(a.toUpperCase(Locale.ROOT), b.toUpperCase(Locale.ROOT));
    }
}
