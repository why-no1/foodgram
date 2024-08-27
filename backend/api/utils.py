from users.models import SubscriptionAuthor


def is_subscribed(user, author):
    if user.is_anonymous:
        return False
    return SubscriptionAuthor.objects.filter(user=user, author=author).exists()
