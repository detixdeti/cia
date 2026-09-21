package de.shop.payment;

public class PayPalProcessor implements PaymentProvider {
    @Override
    public boolean authorize(String orderId, double amount, String token) {
        return token != null && token.contains("PAYPAL");
    }

    @Override
    public boolean capture(String orderId, double amount) {
        return true;
    }

    @Override
    public boolean refund(String transactionId, double amount) {
        return true;
    }
}
