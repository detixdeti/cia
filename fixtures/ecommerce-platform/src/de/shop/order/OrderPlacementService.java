package de.shop.order;

import de.shop.cart.Cart;
import de.shop.cart.CartItem;
import de.shop.inventory.StockService;
import java.util.UUID;

public class OrderPlacementService {
    private OrderRepository orderRepo;
    private StockService stockService;

    public OrderPlacementService(OrderRepository repo, StockService stockService) {
        this.orderRepo = repo;
        this.stockService = stockService;
    }

    public Order placeOrder(Cart cart, double finalTotal) {
        String orderId = "ORD-" + UUID.randomUUID().toString().substring(0, 8);
        Order order = new Order(orderId, cart.getCustomerId(), finalTotal);
        for (CartItem item : cart.getItems()) {
            order.addItem(new OrderItem(item.getSku(), item.getProductName(), item.getQuantity(), item.getUnitPrice()));
            stockService.reserveStock(item.getSku(), item.getQuantity());
        }
        orderRepo.save(order);
        return order;
    }
}
