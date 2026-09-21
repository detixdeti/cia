package de.shop.catalog;

public class ProductVariant {
    private String variantId;
    private String parentProductId;
    private String size;
    private String color;
    private double priceAdjustment;

    public ProductVariant(String variantId, String parentProductId, String size, String color) {
        this.variantId = variantId;
        this.parentProductId = parentProductId;
        this.size = size;
        this.color = color;
    }

    public String getVariantId() { return variantId; }
    public String getParentProductId() { return parentProductId; }
    public String getSize() { return size; }
    public String getColor() { return color; }
    public double getPriceAdjustment() { return priceAdjustment; }
    public void setPriceAdjustment(double adj) { this.priceAdjustment = adj; }
}
