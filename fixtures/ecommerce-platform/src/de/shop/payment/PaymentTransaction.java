package de.shop.payment;

import java.util.Date;

public class PaymentTransaction {
    private String transactionId;
    private String orderId;
    private double amount;
    private String paymentMethod;
    private String status;
    private Date timestamp;

    public PaymentTransaction(String txId, String orderId, double amount, String method) {
        this.transactionId = txId;
        this.orderId = orderId;
        this.amount = amount;
        this.paymentMethod = method;
        this.status = "INITIALIZED";
        this.timestamp = new Date();
    }

    public String getTransactionId() { return transactionId; }
    public String getOrderId() { return orderId; }
    public double getAmount() { return amount; }
    public String getPaymentMethod() { return paymentMethod; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
