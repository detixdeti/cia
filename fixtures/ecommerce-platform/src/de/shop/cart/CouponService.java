package de.shop.cart;

import java.util.HashMap;
import java.util.Map;

public class CouponService {
    private Map<String, Double> validCoupons = new HashMap<>();

    public CouponService() {
        validCoupons.put("WELCOME10", 0.10);
        validCoupons.put("SUMMER20", 0.20);
    }

    public boolean isValid(String code) {
        return validCoupons.containsKey(code);
    }

    public double getDiscountRate(String code) {
        return validCoupons.getOrDefault(code, 0.0);
    }
}
