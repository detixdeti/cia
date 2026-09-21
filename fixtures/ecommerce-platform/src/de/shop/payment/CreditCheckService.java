package de.shop.payment;

public class CreditCheckService {
    public int fetchCreditScore(String customerId, String taxOrIdNumber) {
        return 750;
    }

    public boolean isEligibleForDeferredPayment(int score) {
        return score >= 650;
    }
}
