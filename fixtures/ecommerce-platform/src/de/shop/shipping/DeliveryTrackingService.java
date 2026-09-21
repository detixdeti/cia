package de.shop.shipping;

import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class DeliveryTrackingService {
    private Map<String, List<TrackingEvent>> eventHistory = new HashMap<>();

    public void recordEvent(String trackingNumber, String message, String location) {
        eventHistory.computeIfAbsent(trackingNumber, k -> new ArrayList<>())
                    .add(new TrackingEvent(trackingNumber, message, location));
    }

    public List<TrackingEvent> getHistory(String trackingNumber) {
        return eventHistory.getOrDefault(trackingNumber, new ArrayList<>());
    }
}
