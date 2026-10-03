package de.shop.notification;

public class EmailNotification {
    private String recipient;
    private String subject;
    private String bodyText;

    public EmailNotification(String recipient, String subject, String bodyText) {
        this.recipient = recipient;
        this.subject = subject;
        this.bodyText = bodyText;
    }

    public String getRecipient() { return recipient; }
    public String getSubject() { return subject; }
    public String getBodyText() { return bodyText; }
}
