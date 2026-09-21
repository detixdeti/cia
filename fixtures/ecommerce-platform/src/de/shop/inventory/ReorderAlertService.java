package de.shop.inventory;

import java.util.List;
import java.util.ArrayList;

public class ReorderAlertService {
    public List<String> checkLowStock(List<InventoryItem> items) {
        List<String> lowSkus = new ArrayList<>();
        for (InventoryItem item : items) {
            if (item.getAvailableQuantity() <= item.getReorderThreshold()) {
                lowSkus.add(item.getSku());
            }
        }
        return lowSkus;
    }
}
