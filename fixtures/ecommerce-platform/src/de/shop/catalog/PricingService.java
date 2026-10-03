package de.shop.catalog;

public class PricingService {
    public double calculateNetPrice(Product product, double discountPercent) {
        double base = product.getBasePrice();
        return base * (1.0 - discountPercent);
    }

    public double calculateGrossPrice(double netPrice, double vatRate) {
        return netPrice * (1.0 + vatRate);
    }

    public void updateBasePrice(Product product, double newPrice) {
        if (newPrice > 0) {
            product.setBasePrice(newPrice);
        }
    }
}
