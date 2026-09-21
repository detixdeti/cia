package de.shop.catalog;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

public class ProductRepository {
    private Map<String, Product> storage = new HashMap<>();

    public Product findById(String id) { return storage.get(id); }
    public void save(Product p) { storage.put(p.getId(), p); }
    public List<Product> findAll() { return new ArrayList<>(storage.values()); }
}
