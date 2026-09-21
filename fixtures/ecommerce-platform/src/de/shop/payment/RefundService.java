package de.shop.payment;

public class RefundService {
    private PaymentLedger ledger;

    public RefundService(PaymentLedger ledger) {
        this.ledger = ledger;
    }

    public boolean processRefund(String originalTxId, double refundAmount) {
        PaymentTransaction tx = ledger.getTransaction(originalTxId);
        if (tx != null && tx.getAmount() >= refundAmount) {
            ledger.recordRefund(originalTxId, refundAmount);
            return true;
        }
        return false;
    }
}
