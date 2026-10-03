package de.shop.order;

public class OrderStatusManager {
    private OrderRepository orderRepo;

    public OrderStatusManager(OrderRepository repo) {
        this.orderRepo = repo;
    }

    public void transition(String orderId, OrderStatus nextStatus) {
        Order o = orderRepo.findById(orderId);
        if (o != null) {
            o.setStatus(nextStatus);
            orderRepo.save(o);
        }
    }

    public OrderStatus queryStatus(String orderId) {
        Order o = orderRepo.findById(orderId);
        return o != null ? o.getStatus() : null;
    }
}
