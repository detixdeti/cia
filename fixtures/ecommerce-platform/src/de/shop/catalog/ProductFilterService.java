package de.shop.catalog;

import java.util.List;
import java.util.ArrayList;

public class ProductFilterService {
    public List<Product> filterByPriceRange(List<Product> products, double min, double max) {
        List<Product> res = new ArrayList<>();
        for (Product p : products) {
            if (p.getBasePrice() >= min && p.getBasePrice() <= max) {
                res.add(p);
            }
        }
        return res;
    }

    public List<Product> filterByCategory(List<Product> products, String categoryId) {
        List<Product> res = new ArrayList<>();
        for (Product p : products) {
            if (categoryId.equals(p.getCategoryId())) {
                res.add(p);
            }
        }
        return res;
    }
}
