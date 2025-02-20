# users/views.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_first_screen():
    """
    Первый экран (при /start): одна кнопка Start -> go_to_second_screen
    """
    text = (
        "Any photo in 30 sec\n\n"
        "What can this bot do?\n\n"
        "Just send your selfie to the bot and it will create your portraits in any style you like!\n"
    )
    keyboard = [
        [InlineKeyboardButton("Start", callback_data="go_to_second_screen")]
    ]
    return text, InlineKeyboardMarkup(keyboard)


def get_second_screen():
    """
    Второй экран (главное меню).
    Содержит 5 кнопок, каждая в своей строке: How it works?, Upload photos, Invite friends, Support, Pay
    """
    text = (
        "Photo studio in your pocket!\n\n"
        "40 seconds\n\n"
        "Hello! I'm Cheese Bot 🤘\n"
        "I'm an AI for creating any photo or video with your face.\n\n"
        "How does it work?\n"
        "You can learn more by clicking the button below.\n"
        "Or, if you're ready, you can pay and then upload your photos!"
    )
    keyboard = [
        [InlineKeyboardButton("How it works?", callback_data="how_it_works")],
        [InlineKeyboardButton("Upload photos", callback_data="upload_photos")],
        [InlineKeyboardButton("Invite friends", callback_data="invite_friends")],
        [InlineKeyboardButton("Support", callback_data="support")],
        [InlineKeyboardButton("Pay", callback_data="pay")]  # ВАЖНО: кнопка оплаты
    ]
    return text, InlineKeyboardMarkup(keyboard)


def get_how_it_works_screen():
    """
    Экран "How it works?" с двумя кнопками (каждая в своей строке):
    1) Got it, next
    2) Back -> возвращает на второй экран
    """
    text = (
        "Upload a photo and the result will amaze you!\n\n"
        "I am NeuroPix AI \U0001F916\n"
        "First, I learn from 10 of your photos to create your personal avatar.\n"
        "After that, I can generate any photo with your facial features.\n"
        "Impressive, right?\n"
    )
    keyboard = [
        [InlineKeyboardButton("Got it, next", callback_data="how_it_works_next")],
        [InlineKeyboardButton("Back", callback_data="go_back")]
    ]
    return text, InlineKeyboardMarkup(keyboard)


def get_invite_friends_screen():
    """
    Экран "Invite friends" — возвращает только текст (можно добавить кнопки, если надо).
    """
    text = (
        "Invite 5 friends who will pay for the service.\n"
        "Once they do, you get 20 free photos!\n"
    )
    return text


def get_support_screen():
    """
    Экран "Support" — тоже только текст.
    """
    text = (
        "For support, contact @YourSupportUsername or email: support@example.com"
    )
    return text


def get_payment_screen():
    """
    Экран оплаты с одной кнопкой "Stripe" и кнопкой "Back".
    """
    text = (
        "It's time to proceed with payment!\n"
        "We've lowered the price!\n\n"
        "5$ \n\n"
        "You will get:\n"
        "• 100 photos\n"
        "• 40 photos to choose from\n"
        "• 1 avatar\n"
        "• Access to 'God mode'\n"
        "• Excitement from the generated photos!\n\n"
        "Choose a payment method:"
    )
    keyboard = [
        [InlineKeyboardButton("Stripe", callback_data="bank_cards")],
        [InlineKeyboardButton("Back", callback_data="go_back")]
    ]
    return text, InlineKeyboardMarkup(keyboard)
