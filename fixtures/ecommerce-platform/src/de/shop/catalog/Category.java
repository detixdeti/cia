package de.shop.catalog;

import java.util.List;
import java.util.ArrayList;

public class Category {
    private String id;
    private String name;
    private String parentId;
    private List<String> subCategoryIds = new ArrayList<>();

    public Category(String id, String name, String parentId) {
        this.id = id;
        this.name = name;
        this.parentId = parentId;
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public String getParentId() { return parentId; }
    public List<String> getSubCategoryIds() { return subCategoryIds; }
    public void addSubCategory(String subId) { subCategoryIds.add(subId); }
}
