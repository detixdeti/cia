package de.shop.cart;

import java.util.HashMap;
import java.util.Map;

public class WishlistService {
    private Map<String, Wishlist> wishlists = new HashMap<>();
    private CartService cartService;

    public WishlistService(CartService cartService) {
        this.cartService = cartService;
    }

    public void addToWishlist(String customerId, String sku) {
        Wishlist w = wishlists.computeIfAbsent(customerId, Wishlist::new);
        w.addItem(new WishlistItem(sku));
    }

    public void moveToCart(String customerId, String sku, String name, double price) {
        Wishlist w = wishlists.get(customerId);
        if (w != null) {
            w.removeItem(sku);
            cartService.addToCart(customerId, sku, name, 1, price);
        }
    }
}
