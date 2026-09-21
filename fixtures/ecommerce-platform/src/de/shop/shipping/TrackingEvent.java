package de.shop.shipping;

import java.util.Date;

public class TrackingEvent {
    private String trackingNumber;
    private String description;
    private String location;
    private Date eventTime;

    public TrackingEvent(String trackingNumber, String description, String location) {
        this.trackingNumber = trackingNumber;
        this.description = description;
        this.location = location;
        this.eventTime = new Date();
    }

    public String getTrackingNumber() { return trackingNumber; }
    public String getDescription() { return description; }
    public String getLocation() { return location; }
    public Date getEventTime() { return eventTime; }
}
