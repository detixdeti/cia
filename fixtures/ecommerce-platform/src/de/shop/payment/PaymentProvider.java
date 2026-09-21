package de.shop.payment;

public interface PaymentProvider {
    boolean authorize(String orderId, double amount, String token);
    boolean capture(String orderId, double amount);
    boolean refund(String transactionId, double amount);
}
