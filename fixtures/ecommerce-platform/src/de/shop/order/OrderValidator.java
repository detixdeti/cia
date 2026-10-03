package de.shop.order;

import de.shop.cart.Cart;

public class OrderValidator {
    private double minimumOrderValue = 10.0;

    public boolean validateCart(Cart cart) {
        return cart != null && !cart.getItems().isEmpty();
    }

    public boolean checkMinimumOrderValue(double totalAmount) {
        return totalAmount >= minimumOrderValue;
    }

    public void setMinimumOrderValue(double val) {
        this.minimumOrderValue = val;
    }
}
