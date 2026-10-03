package de.shop.support;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

public class TicketManagementService {
    private Map<String, SupportTicket> tickets = new HashMap<>();

    public SupportTicket openTicket(String customerId, String issue) {
        String id = "TCK-" + UUID.randomUUID().toString().substring(0, 6);
        SupportTicket ticket = new SupportTicket(id, customerId, issue);
        tickets.put(id, ticket);
        return ticket;
    }

    public void answerTicket(String ticketId, String reply, boolean close) {
        SupportTicket t = tickets.get(ticketId);
        if (t != null && close) {
            t.setStatus("RESOLVED");
        }
    }
}
