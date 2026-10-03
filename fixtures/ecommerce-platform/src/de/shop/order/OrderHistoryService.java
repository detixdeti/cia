package de.shop.order;

import java.util.List;

public class OrderHistoryService {
    private OrderRepository orderRepo;

    public OrderHistoryService(OrderRepository repo) {
        this.orderRepo = repo;
    }

    public List<Order> getCustomerOrders(String customerId) {
        return orderRepo.findByCustomerId(customerId);
    }
}
