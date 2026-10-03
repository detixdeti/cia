package de.shop.shipping;

import java.util.UUID;

public class ShippingLabelService {
    public Shipment generateLabel(String orderId, String carrier) {
        String trackingNum = "TRK-" + carrier.toUpperCase() + "-" + UUID.randomUUID().toString().substring(0, 8);
        return new Shipment(trackingNum, orderId, carrier);
    }
}
