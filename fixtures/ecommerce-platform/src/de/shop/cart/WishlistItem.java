package de.shop.cart;

import java.util.Date;

public class WishlistItem {
    private String sku;
    private Date addedAt;

    public WishlistItem(String sku) {
        this.sku = sku;
        this.addedAt = new Date();
    }

    public String getSku() { return sku; }
    public Date getAddedAt() { return addedAt; }
}
