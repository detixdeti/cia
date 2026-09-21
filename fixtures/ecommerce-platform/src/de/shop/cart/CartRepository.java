package de.shop.cart;

import java.util.HashMap;
import java.util.Map;

public class CartRepository {
    private Map<String, Cart> storage = new HashMap<>();

    public Cart findByCustomerId(String customerId) {
        return storage.get(customerId);
    }

    public void save(Cart cart) {
        storage.put(cart.getCustomerId(), cart);
    }
}
