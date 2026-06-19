def notifications(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False).count()
        unread_msgs = 0
        for conv in request.user.conversations.all():
            unread_msgs += conv.messages.filter(
                is_read=False).exclude(sender=request.user).count()
        return {
            'unread_notifications': unread,
            'unread_messages': unread_msgs,
        }
    return {'unread_notifications': 0, 'unread_messages': 0}
