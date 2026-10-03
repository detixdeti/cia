package de.shop.catalog;

public class Product {
    private String id;
    private String sku;
    private String name;
    private String description;
    private double basePrice;
    private String categoryId;
    private boolean active;

    public Product(String id, String sku, String name, double basePrice, String categoryId) {
        this.id = id;
        this.sku = sku;
        this.name = name;
        this.basePrice = basePrice;
        this.categoryId = categoryId;
        this.active = true;
    }

    public String getId() { return id; }
    public String getSku() { return sku; }
    public String getName() { return name; }
    public String getDescription() { return description; }
    public void setDescription(String desc) { this.description = desc; }
    public double getBasePrice() { return basePrice; }
    public void setBasePrice(double basePrice) { this.basePrice = basePrice; }
    public String getCategoryId() { return categoryId; }
    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }
}
