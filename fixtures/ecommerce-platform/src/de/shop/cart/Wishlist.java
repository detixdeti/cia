package de.shop.cart;

import java.util.List;
import java.util.ArrayList;

public class Wishlist {
    private String customerId;
    private List<WishlistItem> items = new ArrayList<>();

    public Wishlist(String customerId) {
        this.customerId = customerId;
    }

    public String getCustomerId() { return customerId; }
    public List<WishlistItem> getItems() { return items; }
    public void addItem(WishlistItem item) { items.add(item); }
    public void removeItem(String sku) {
        items.removeIf(i -> i.getSku().equals(sku));
    }
}
