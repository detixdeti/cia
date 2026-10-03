package de.shop.payment;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

public class PaymentLedger {
    private Map<String, PaymentTransaction> transactions = new HashMap<>();

    public void record(PaymentTransaction tx) {
        transactions.put(tx.getTransactionId(), tx);
    }

    public PaymentTransaction getTransaction(String txId) {
        return transactions.get(txId);
    }

    public void recordRefund(String txId, double amount) {
        PaymentTransaction tx = transactions.get(txId);
        if (tx != null) {
            tx.setStatus("REFUNDED_" + amount);
        }
    }

    public List<PaymentTransaction> getAllTransactions() {
        return new ArrayList<>(transactions.values());
    }
}
