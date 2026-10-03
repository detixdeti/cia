package de.shop.payment;

public class CreditCardProcessor implements PaymentProvider {
    @Override
    public boolean authorize(String orderId, double amount, String token) {
        return token != null && token.startsWith("CC_TOK");
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
