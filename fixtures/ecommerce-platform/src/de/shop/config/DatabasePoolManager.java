package de.shop.config;

public class DatabasePoolManager {
    public int getActiveConnections() {
        return 8;
    }

    public boolean isPoolHealthy() {
        return true;
    }
}
