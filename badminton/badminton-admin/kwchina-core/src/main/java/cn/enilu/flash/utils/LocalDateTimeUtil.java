package cn.enilu.flash.utils;

import java.time.*;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

public class LocalDateTimeUtil {
    public static String formatYMDHMS(LocalDateTime time) {
        String f = format(time, "yyyy-MM-dd HH:mm:ss");
        return f == null ? "" : f;
    }

    public static String format(LocalDateTime time, String pattern) {
        if (time == null) {
            return null;
        }

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern(pattern);
        return formatter.format(time);
    }

    public static String format(LocalDate time, String pattern) {
        if (time == null) {
            return null;
        }

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern(pattern);
        return formatter.format(time);
    }


    public static LocalDateTime fromTimestamp(Long ts) {
        if (ts == null) {
            return null;
        }

        return LocalDateTime.ofInstant(Instant.ofEpochMilli(ts), ZoneId.systemDefault());
    }


    /**
     * 根据查询条件返回日期列表
     *
     * 1. 如果同时指定 startDate、endDate则忽略days
     * 2. 如果只指定startDate、endDate其中之一，则以该日期为边界，向后或向前数days，如果days没有传，则默认为7
     * 3. 如果startDate、endDate都是空，endDate默认为当前日期
     *
     * @param startDate
     * @param endDate
     * @param days
     * @return
     */
    public static List<LocalDate> localDatesOnCondition(LocalDate startDate, LocalDate endDate, Integer days) {
        if (days == null) {
            days = 7;
        }

        // 注意，日期计算连头连尾，所以days要减1天
        if (startDate == null && endDate == null) {
            endDate = LocalDate.now();
            startDate = endDate.minusDays(days - 1);
        }

        if (startDate == null && endDate != null) {
            startDate = endDate.minusDays(days - 1);
        }

        if (startDate != null && endDate == null) {
            endDate = startDate.plusDays(days - 1);
        }

        List<LocalDate> ltDate = new ArrayList<>();
        while (!startDate.isAfter(endDate)) {
            ltDate.add(startDate);
            startDate = startDate.plusDays(1);
        }

        return ltDate;
    }

    public static String toDayHours(LocalDate before, LocalDate now) {
        Duration duration = Duration.between(before.atStartOfDay(), LocalDateTime.now());
        return String.format("%d天%d小时", duration.toDaysPart(), duration.toHoursPart());
    }
    public static String toMonthDay(LocalDate before, LocalDate now) {
        Period period = before.until(now);
        return String.format("%d月%d天",
                period.getYears() * 12 + period.getMonths(),
                period.getDays());
    }

    /**
     * 根据查询条件返回月份列表
     *
     * 1. 如果同时指定 startDate、endDate则忽略days
     *
     * @param startDate
     * @param endDate
     * @return
     */
    public static List<String> localMonthOnCondition(LocalDate startDate, LocalDate endDate) {
        List<String> ltDate = new ArrayList<>();
        while (!startDate.isAfter(endDate)) {
            ltDate.add(startDate.getMonthValue()+"月");
            startDate = startDate.plusMonths(1);
        }

        return ltDate;
    }

}
