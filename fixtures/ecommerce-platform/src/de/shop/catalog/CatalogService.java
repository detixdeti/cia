package de.shop.catalog;

import java.util.List;
import java.util.ArrayList;

public class CatalogService {
    private ProductRepository productRepo;
    private SearchIndexService searchIndex;

    public CatalogService(ProductRepository repo, SearchIndexService index) {
        this.productRepo = repo;
        this.searchIndex = index;
    }

    public Product getProduct(String id) {
        return productRepo.findById(id);
    }

    public List<Product> search(String query) {
        return searchIndex.query(query);
    }

    public void addProduct(Product product) {
        productRepo.save(product);
        searchIndex.index(product);
    }

    public void deactivateProduct(String id) {
        Product p = productRepo.findById(id);
        if (p != null) {
            p.setActive(false);
            productRepo.save(p);
            searchIndex.remove(id);
        }
    }
}
