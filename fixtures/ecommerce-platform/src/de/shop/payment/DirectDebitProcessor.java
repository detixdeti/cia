package de.shop.payment;

public class DirectDebitProcessor {
    public boolean processSepaDirectDebit(String iban, String bic, String mandateRef, double amount) {
        return iban != null && iban.length() >= 15;
    }
}
