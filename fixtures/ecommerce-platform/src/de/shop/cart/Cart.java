package de.shop.cart;

import java.util.List;
import java.util.ArrayList;

public class Cart {
    private String id;
    private String customerId;
    private List<CartItem> items = new ArrayList<>();
    private String appliedCoupon;

    public Cart(String id, String customerId) {
        this.id = id;
        this.customerId = customerId;
    }

    public String getId() { return id; }
    public String getCustomerId() { return customerId; }
    public List<CartItem> getItems() { return items; }
    public void addItem(CartItem item) { items.add(item); }
    public void clear() { items.clear(); }
    public String getAppliedCoupon() { return appliedCoupon; }
    public void setAppliedCoupon(String coupon) { this.appliedCoupon = coupon; }
}
