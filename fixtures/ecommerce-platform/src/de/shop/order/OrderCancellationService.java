package de.shop.order;

import de.shop.inventory.StockService;

public class OrderCancellationService {
    private OrderRepository orderRepo;
    private StockService stockService;

    public OrderCancellationService(OrderRepository repo, StockService stockService) {
        this.orderRepo = repo;
        this.stockService = stockService;
    }

    public boolean cancelOrder(String orderId) {
        Order o = orderRepo.findById(orderId);
        if (o == null || o.getStatus() == OrderStatus.SHIPPED || o.getStatus() == OrderStatus.DELIVERED) {
            return false;
        }
        o.setStatus(OrderStatus.CANCELLED);
        for (OrderItem item : o.getItems()) {
            stockService.releaseReservedStock(item.getSku(), item.getQuantity());
        }
        orderRepo.save(o);
        return true;
    }
}
