package de.shop.notification;

public class MailSenderService {
    public boolean send(EmailNotification notification) {
        return notification != null && notification.getRecipient() != null;
    }
}
