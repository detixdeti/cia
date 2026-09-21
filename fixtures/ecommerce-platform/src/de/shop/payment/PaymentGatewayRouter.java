package de.shop.payment;

public class PaymentGatewayRouter {
    private CreditCardProcessor ccProcessor;
    private PayPalProcessor paypalProcessor;

    public PaymentGatewayRouter(CreditCardProcessor cc, PayPalProcessor pp) {
        this.ccProcessor = cc;
        this.paypalProcessor = pp;
    }

    public PaymentProvider route(String paymentType) {
        if ("CREDIT_CARD".equalsIgnoreCase(paymentType)) return ccProcessor;
        if ("PAYPAL".equalsIgnoreCase(paymentType)) return paypalProcessor;
        return null;
    }
}
