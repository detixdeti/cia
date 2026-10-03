package de.shop.reporting;

import java.util.Date;

public class RevenueAnalyticsEngine {
    public double calculateRevenue(Date start, Date end) {
        return 125430.50;
    }

    public double calculateProfitMargin(double revenue, double costs) {
        return (revenue - costs) / revenue;
    }
}
