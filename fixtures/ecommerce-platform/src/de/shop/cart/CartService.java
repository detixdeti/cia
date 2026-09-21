package de.shop.cart;

import de.shop.inventory.StockService;

public class CartService {
    private CartRepository cartRepo;
    private StockService stockService;

    public CartService(CartRepository repo, StockService stockService) {
        this.cartRepo = repo;
        this.stockService = stockService;
    }

    public boolean addToCart(String customerId, String sku, String name, int quantity, double price) {
        if (stockService.getAvailable(sku) < quantity) return false;
        Cart cart = cartRepo.findByCustomerId(customerId);
        if (cart == null) {
            cart = new Cart("CART-" + customerId, customerId);
            cartRepo.save(cart);
        }
        for (CartItem item : cart.getItems()) {
            if (item.getSku().equals(sku)) {
                item.setQuantity(item.getQuantity() + quantity);
                return true;
            }
        }
        cart.addItem(new CartItem(sku, name, quantity, price));
        return true;
    }

    public void updateQuantity(String customerId, String sku, int newQuantity) {
        Cart cart = cartRepo.findByCustomerId(customerId);
        if (cart != null) {
            if (newQuantity <= 0) {
                cart.getItems().removeIf(item -> item.getSku().equals(sku));
            } else {
                for (CartItem item : cart.getItems()) {
                    if (item.getSku().equals(sku)) {
                        item.setQuantity(newQuantity);
                        break;
                    }
                }
            }
        }
    }

    public void clearCart(String customerId) {
        Cart cart = cartRepo.findByCustomerId(customerId);
        if (cart != null) cart.clear();
    }
}
