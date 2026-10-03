package de.shop.shipping;

public class PackingStationValidator {
    public boolean validatePackstation(String postNumber, String stationId) {
        return postNumber != null && stationId != null && stationId.matches("\\d{3,4}");
    }
}
