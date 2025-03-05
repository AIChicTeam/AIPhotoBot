# users/views.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from uuid import uuid4
from asgiref.sync import sync_to_async
from .models import Referral

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
        [InlineKeyboardButton("Pay", callback_data="pay")]  
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



def get_upload_instructions_screen():
    """
    Сообщение, которое показывается пользователю, когда он оплатил
    и нажимает "Upload photos".
    """
    text = (
        "Congratulations, your payment was successful!\n"
        "Now you can upload 10 photos. After that, you'll get 10 AI-generated images with your avatar.\n\n"
        "Important points:\n"
        "• The photos must only include you.\n"
        "• Avoid photos with extreme facial expressions.\n"
        "• Use different angles and outfits.\n"
        "• Good lighting = better results.\n"
        "• If iPhone asks \"Convert to JPEG\", please accept.\n"
        "• You can only upload photos once.\n\n"
        "Please choose your photos carefully and follow the instructions!"
    )
    
    keyboard = [
        [InlineKeyboardButton("Back", callback_data="go_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return text, reply_markup

    

@sync_to_async
def get_or_create_referral(telegram_user_id):
    return Referral.objects.get_or_create(user_id=telegram_user_id)

async def get_invite_friends_screen(telegram_user_id):
    referral, created = await get_or_create_referral(telegram_user_id)
    referral_link = f"https://t.me/AIMelnykBot?start=ref_{referral.referral_code}"

    text = (
        "Invite your friends and get bonuses!\n\n"
        "Share this link with your friends:\n"
        f"{referral_link}\n\n"
        "If they pay for the service, you will get 5 extra generations!"
    )

    keyboard = [
        [InlineKeyboardButton("Copy link", url=referral_link)],
        [InlineKeyboardButton("Back", callback_data="go_back")]
    ]

    return text, InlineKeyboardMarkup(keyboard)




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
        [InlineKeyboardButton("Pay with Stars", callback_data="buy_stars")],
        [InlineKeyboardButton("Back", callback_data="go_back")]
    ]
    return text, InlineKeyboardMarkup(keyboard)
