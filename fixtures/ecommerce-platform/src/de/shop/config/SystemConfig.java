package de.shop.config;

public class SystemConfig {
    private String environment = "PRODUCTION";
    private boolean maintenanceMode = false;

    public String getEnvironment() { return environment; }
    public boolean isMaintenanceMode() { return maintenanceMode; }
    public void setMaintenanceMode(boolean mode) { this.maintenanceMode = mode; }
}
