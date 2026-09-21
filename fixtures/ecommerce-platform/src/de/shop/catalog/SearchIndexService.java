package de.shop.catalog;

import java.util.List;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

public class SearchIndexService {
    private Map<String, Product> indexedProducts = new HashMap<>();

    public void index(Product product) {
        indexedProducts.put(product.getId(), product);
    }

    public void remove(String productId) {
        indexedProducts.remove(productId);
    }

    public List<Product> query(String text) {
        List<Product> matches = new ArrayList<>();
        String lower = text.toLowerCase();
        for (Product p : indexedProducts.values()) {
            if (p.getName().toLowerCase().contains(lower) || 
               (p.getDescription() != null && p.getDescription().toLowerCase().contains(lower))) {
                matches.add(p);
            }
        }
        return matches;
    }
}
