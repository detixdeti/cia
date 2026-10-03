package de.shop.order;

import java.util.List;
import java.util.ArrayList;
import java.util.Date;

public class Order {
    private String orderId;
    private String customerId;
    private List<OrderItem> items = new ArrayList<>();
    private double totalAmount;
    private OrderStatus status;
    private Date createdAt;

    public Order(String orderId, String customerId, double totalAmount) {
        this.orderId = orderId;
        this.customerId = customerId;
        this.totalAmount = totalAmount;
        this.status = OrderStatus.PENDING;
        this.createdAt = new Date();
    }

    public String getOrderId() { return orderId; }
    public String getCustomerId() { return customerId; }
    public List<OrderItem> getItems() { return items; }
    public void addItem(OrderItem item) { items.add(item); }
    public double getTotalAmount() { return totalAmount; }
    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus status) { this.status = status; }
    public Date getCreatedAt() { return createdAt; }
}
