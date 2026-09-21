package de.shop.notification;

public class NotificationTemplateEngine {
    public String renderOrderConfirmation(String orderId, double amount) {
        return "Vielen Dank fuer Ihre Bestellung " + orderId + " ueber " + amount + " EUR.";
    }

    public String renderShippingNotice(String orderId, String trackingNumber) {
        return "Ihre Bestellung " + orderId + " wurde versandt. Tracking: " + trackingNumber;
    }
}
