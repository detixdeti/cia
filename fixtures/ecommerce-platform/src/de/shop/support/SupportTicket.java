package de.shop.support;

import java.util.Date;

public class SupportTicket {
    private String ticketId;
    private String customerId;
    private String issueDescription;
    private String status;
    private Date createdAt;

    public SupportTicket(String ticketId, String customerId, String issueDescription) {
        this.ticketId = ticketId;
        this.customerId = customerId;
        this.issueDescription = issueDescription;
        this.status = "OPEN";
        this.createdAt = new Date();
    }

    public String getTicketId() { return ticketId; }
    public String getCustomerId() { return customerId; }
    public String getIssueDescription() { return issueDescription; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
}
