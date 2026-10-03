package de.shop.order;

public class OrderItem {
    private String sku;
    private String name;
    private int quantity;
    private double unitPrice;

    public OrderItem(String sku, String name, int quantity, double unitPrice) {
        this.sku = sku;
        this.name = name;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
    }

    public String getSku() { return sku; }
    public String getName() { return name; }
    public int getQuantity() { return quantity; }
    public double getUnitPrice() { return unitPrice; }
}
