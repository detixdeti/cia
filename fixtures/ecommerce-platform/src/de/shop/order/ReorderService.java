package de.shop.order;

import de.shop.cart.CartService;

public class ReorderService {
    private OrderRepository orderRepo;
    private CartService cartService;

    public ReorderService(OrderRepository repo, CartService cartService) {
        this.orderRepo = repo;
        this.cartService = cartService;
    }

    public boolean reorder(String orderId, String customerId) {
        Order prev = orderRepo.findById(orderId);
        if (prev == null) return false;
        for (OrderItem item : prev.getItems()) {
            cartService.addToCart(customerId, item.getSku(), item.getName(), item.getQuantity(), item.getUnitPrice());
        }
        return true;
    }
}
