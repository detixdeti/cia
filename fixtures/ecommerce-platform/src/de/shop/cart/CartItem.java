package de.shop.cart;

public class CartItem {
    private String sku;
    private String productName;
    private int quantity;
    private double unitPrice;

    public CartItem(String sku, String productName, int quantity, double unitPrice) {
        this.sku = sku;
        this.productName = productName;
        this.quantity = quantity;
        this.unitPrice = unitPrice;
    }

    public String getSku() { return sku; }
    public String getProductName() { return productName; }
    public int getQuantity() { return quantity; }
    public void setQuantity(int q) { this.quantity = q; }
    public double getUnitPrice() { return unitPrice; }
    public double getTotalPrice() { return unitPrice * quantity; }
}
