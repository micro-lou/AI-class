package cn.enilu.flash.utils;

import java.math.BigDecimal;

public class EloUtils {

    private final static BigDecimal DONE = new BigDecimal("1.0");
    private final static BigDecimal D400 = new BigDecimal("400.0");

    public static double rating(int ra, int rb) {
        return 1.0 / (1.0 + Math.pow(10, (ra - rb) / 400.0));
    }


}
