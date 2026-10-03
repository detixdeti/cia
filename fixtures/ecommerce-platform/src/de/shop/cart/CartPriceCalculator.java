package de.shop.cart;

public class CartPriceCalculator {
    private CouponService couponService;

    public CartPriceCalculator(CouponService couponService) {
        this.couponService = couponService;
    }

    public double calculateSubtotal(Cart cart) {
        double subtotal = 0.0;
        for (CartItem item : cart.getItems()) {
            subtotal += item.getTotalPrice();
        }
        return subtotal;
    }

    public double calculateTotal(Cart cart) {
        double subtotal = calculateSubtotal(cart);
        if (cart.getAppliedCoupon() != null && couponService.isValid(cart.getAppliedCoupon())) {
            double rate = couponService.getDiscountRate(cart.getAppliedCoupon());
            subtotal *= (1.0 - rate);
        }
        return subtotal;
    }
}
