package de.shop.order;

import de.shop.cart.Cart;
import de.shop.cart.CartPriceCalculator;

public class CheckoutService {
    private OrderValidator validator;
    private CartPriceCalculator priceCalc;

    public CheckoutService(OrderValidator validator, CartPriceCalculator priceCalc) {
        this.validator = validator;
        this.priceCalc = priceCalc;
    }

    public boolean canCheckout(Cart cart) {
        return validator.validateCart(cart) && validator.checkMinimumOrderValue(priceCalc.calculateTotal(cart));
    }
}
