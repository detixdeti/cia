package de.shop.inventory;

public class InventoryItem {
    private String sku;
    private int quantityOnHand;
    private int quantityReserved;
    private int reorderThreshold;

    public InventoryItem(String sku, int quantityOnHand, int reorderThreshold) {
        this.sku = sku;
        this.quantityOnHand = quantityOnHand;
        this.quantityReserved = 0;
        this.reorderThreshold = reorderThreshold;
    }

    public String getSku() { return sku; }
    public int getQuantityOnHand() { return quantityOnHand; }
    public void addStock(int count) { this.quantityOnHand += count; }
    public int getQuantityReserved() { return quantityReserved; }
    public void setQuantityReserved(int count) { this.quantityReserved = count; }
    public int getAvailableQuantity() { return quantityOnHand - quantityReserved; }
    public int getReorderThreshold() { return reorderThreshold; }
}
