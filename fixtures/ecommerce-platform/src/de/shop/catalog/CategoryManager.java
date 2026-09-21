package de.shop.catalog;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.ArrayList;

public class CategoryManager {
    private Map<String, Category> categories = new HashMap<>();

    public void addCategory(Category category) {
        categories.put(category.getId(), category);
    }

    public Category getCategory(String id) {
        return categories.get(id);
    }

    public List<Category> getRootCategories() {
        List<Category> roots = new ArrayList<>();
        for (Category c : categories.values()) {
            if (c.getParentId() == null) roots.add(c);
        }
        return roots;
    }
}
