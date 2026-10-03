package de.shop.inventory;

import java.util.List;
import java.util.ArrayList;

public class WarehouseManager {
    private String locationCode;

    public WarehouseManager(String locationCode) {
        this.locationCode = locationCode;
    }

    public String locateShelf(String sku) {
        return "AISLE-" + (Math.abs(sku.hashCode()) % 20) + "-RACK-3";
    }

    public boolean isWarehouseOperational() {
        return true;
    }
}
