package de.shop.order;

import java.util.UUID;

public class InvoiceGenerator {
    public Invoice createInvoice(Order order) {
        String invNum = "INV-" + UUID.randomUUID().toString().substring(0, 8);
        double total = order.getTotalAmount();
        double vat = total * 0.19 / 1.19;
        return new Invoice(invNum, order.getOrderId(), total, vat);
    }
}
