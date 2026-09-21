package de.shop.catalog;

import java.util.List;

public class CatalogExporter {
    public String exportToCsv(List<Product> products) {
        StringBuilder sb = new StringBuilder("SKU;NAME;PRICE;CATEGORY\n");
        for (Product p : products) {
            sb.append(p.getSku()).append(";")
              .append(p.getName()).append(";")
              .append(p.getBasePrice()).append(";")
              .append(p.getCategoryId()).append("\n");
        }
        return sb.toString();
    }
}
