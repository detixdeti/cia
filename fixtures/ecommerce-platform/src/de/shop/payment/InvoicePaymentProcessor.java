package de.shop.payment;

public class InvoicePaymentProcessor {
    public boolean approveInvoicePayment(String customerId, double amount, double creditLimit) {
        return amount <= creditLimit;
    }
}
