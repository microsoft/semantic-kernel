// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.MockedStatic;

import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.Locale;

@SuppressWarnings("ReturnValueIgnored")
public class TimeSkillTest {
    private static final ZonedDateTime mockDateTime;

    static {
        mockDateTime = ZonedDateTime.of(2025, 1, 12, 9, 15, 7, 0, ZoneId.systemDefault());
    }

    @Test
    public void testDate() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.date();
            assertEquals("Sunday, January 12, 2025", result);
        }
    }

    @Test
    public void testTime() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.time();
            assertEqualsIgnoreCase("09:15:07 AM", result);
        }
    }

    @Test
    public void testToday() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.today();
            assertEquals("Sunday, January 12, 2025", result);
        }
    }

    @Test
    public void testNow() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.now();
            assertEqualsIgnoreCase("Sunday, January 12, 2025 9:15 AM", result);
        }
    }

    @Test
    public void testYear() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.year();
            assertEquals("2025", result);
        }
    }

    @Test
    public void testMonth() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.month();
            assertEquals("January", result);
        }
    }

    @Test
    public void testMonthNumber() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.monthNumber();
            assertEquals("01", result);
        }
    }

    @Test
    public void testDay() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.day();
            assertEquals("12", result);
        }
    }

    @Test
    public void testDayOfWeek() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.dayOfWeek();
            assertEquals("Sunday", result);
        }
    }

    public void assertEqualsIgnoreCase(String a, String b) {
        Assertions.assertEquals(a.toUpperCase(Locale.ROOT), b.toUpperCase(Locale.ROOT));
    }

    @Test
    public void testHour() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.hour();
            assertEqualsIgnoreCase("9 AM", result);
        }
    }

    @Test
    public void testHourNumber() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.hourNumber();
            assertEquals("09", result);
        }
    }

    @Test
    public void testMinute() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.minute();
            assertEquals("15", result);
        }
    }

    @Test
    public void testSecond() {
        TimeSkill timeSkill = new TimeSkill();

        try (MockedStatic<ZonedDateTime> mocked = mockStatic(ZonedDateTime.class)) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            String result = timeSkill.second();
            assertEquals("07", result);
        }
    }

    @Test
    public void daysAgo() {
        try (MockedStatic<ZonedDateTime> mocked =
                mockStatic(
                        ZonedDateTime.class,
                        withSettings()
                                .useConstructor()
                                .outerInstance(mockDateTime)
                                .defaultAnswer(CALLS_REAL_METHODS))) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            assertEquals("Thursday, January 9, 2025", TimeSkill.daysAgo("3"));
            assertEquals("Tuesday, January 7, 2025", TimeSkill.daysAgo("5"));
        }
    }

    @Test
    public void testDateMatchingLastDayName() {
        try (MockedStatic<ZonedDateTime> mocked =
                mockStatic(
                        ZonedDateTime.class,
                        withSettings()
                                .useConstructor()
                                .outerInstance(mockDateTime)
                                .defaultAnswer(CALLS_REAL_METHODS))) {
            mocked.when(ZonedDateTime::now).thenReturn(mockDateTime);

            assertEquals("Sunday, January 5, 2025", TimeSkill.dateMatchingLastDayName("Sunday"));
            assertEquals("Monday, January 6, 2025", TimeSkill.dateMatchingLastDayName("Monday"));
            assertEquals("Tuesday, January 7, 2025", TimeSkill.dateMatchingLastDayName("Tuesday"));
            assertEquals(
                    "Wednesday, January 8, 2025", TimeSkill.dateMatchingLastDayName("wednesday"));
            assertEquals(
                    "Thursday, January 9, 2025", TimeSkill.dateMatchingLastDayName("thursday"));
            assertEquals("Friday, January 10, 2025", TimeSkill.dateMatchingLastDayName("Friday"));
            assertEquals(
                    "Saturday, January 11, 2025", TimeSkill.dateMatchingLastDayName("Saturday"));
        }
    }
}
