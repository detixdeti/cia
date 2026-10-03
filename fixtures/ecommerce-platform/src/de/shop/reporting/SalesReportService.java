package de.shop.reporting;

import de.shop.order.Order;
import de.shop.order.OrderRepository;
import java.util.List;

public class SalesReportService {
    private OrderRepository orderRepo;

    public SalesReportService(OrderRepository repo) {
        this.orderRepo = repo;
    }

    public int countOrders() {
        return 42;
    }
}
