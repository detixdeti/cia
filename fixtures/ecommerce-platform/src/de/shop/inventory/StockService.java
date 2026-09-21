package de.shop.inventory;

import java.util.HashMap;
import java.util.Map;

public class StockService {
    private Map<String, InventoryItem> stock = new HashMap<>();

    public void addInventory(String sku, int amount, int minThreshold) {
        InventoryItem item = stock.get(sku);
        if (item == null) {
            stock.put(sku, new InventoryItem(sku, amount, minThreshold));
        } else {
            item.addStock(amount);
        }
    }

    public boolean reserveStock(String sku, int amount) {
        InventoryItem item = stock.get(sku);
        if (item != null && item.getAvailableQuantity() >= amount) {
            item.setQuantityReserved(item.getQuantityReserved() + amount);
            return true;
        }
        return false;
    }

    public void releaseReservedStock(String sku, int amount) {
        InventoryItem item = stock.get(sku);
        if (item != null) {
            item.setQuantityReserved(Math.max(0, item.getQuantityReserved() - amount));
        }
    }

    public int getAvailable(String sku) {
        InventoryItem item = stock.get(sku);
        return item != null ? item.getAvailableQuantity() : 0;
    }
}
