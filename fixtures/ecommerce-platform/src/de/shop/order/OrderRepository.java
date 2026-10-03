package de.shop.order;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

public class OrderRepository {
    private Map<String, Order> orders = new HashMap<>();

    public Order findById(String id) { return orders.get(id); }
    public void save(Order order) { orders.put(order.getOrderId(), order); }
    public List<Order> findByCustomerId(String customerId) {
        List<Order> result = new ArrayList<>();
        for (Order o : orders.values()) {
            if (customerId.equals(o.getCustomerId())) result.add(o);
        }
        return result;
    }
}
