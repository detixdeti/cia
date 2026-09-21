package de.shop.shipping;

import java.util.Date;

public class Shipment {
    private String trackingNumber;
    private String orderId;
    private String carrier;
    private String status;
    private Date dispatchedAt;

    public Shipment(String trackingNumber, String orderId, String carrier) {
        this.trackingNumber = trackingNumber;
        this.orderId = orderId;
        this.carrier = carrier;
        this.status = "CREATED";
        this.dispatchedAt = new Date();
    }

    public String getTrackingNumber() { return trackingNumber; }
    public String getOrderId() { return orderId; }
    public String getCarrier() { return carrier; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
