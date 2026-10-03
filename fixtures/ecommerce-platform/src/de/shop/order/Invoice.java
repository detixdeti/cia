package de.shop.order;

import java.util.Date;

public class Invoice {
    private String invoiceNumber;
    private String orderId;
    private double totalAmount;
    private double vatAmount;
    private Date issuedAt;

    public Invoice(String invoiceNumber, String orderId, double totalAmount, double vatAmount) {
        this.invoiceNumber = invoiceNumber;
        this.orderId = orderId;
        this.totalAmount = totalAmount;
        this.vatAmount = vatAmount;
        this.issuedAt = new Date();
    }

    public String getInvoiceNumber() { return invoiceNumber; }
    public String getOrderId() { return orderId; }
    public double getTotalAmount() { return totalAmount; }
    public double getVatAmount() { return vatAmount; }
    public Date getIssuedAt() { return issuedAt; }
}
