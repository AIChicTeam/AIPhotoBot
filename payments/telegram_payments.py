import structlog
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message, LabeledPrice, PreCheckoutQuery,
    InlineKeyboardMarkup, CallbackQuery
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()
router.message.filter(F.chat.type == "private")
logger = structlog.get_logger()

@router.callback_query(F.data == "buy_stars")
async def on_buy_stars(callback: CallbackQuery):
    """
    Handler for the "buy_stars" button click.
    Creates a Telegram-built-in invoice for purchasing XTR stars.
    """
    # Let's offer to purchase 5 stars
    amount = 5

    # Create a keyboard: a payment button (pay=True) and a "Cancel" button
    kb = InlineKeyboardBuilder()
    kb.button(text=f"Pay {amount} ⭐", pay=True)
    kb.button(text="Cancel", callback_data="donate_cancel")
    kb.adjust(1)

    # For Telegram Stars, the provider_token is left empty
    # currency="XTR" indicates using the Telegram Stars virtual currency
    prices = [LabeledPrice(label="XTR", amount=amount)]

    await callback.message.answer_invoice(
        title="Donate to the author",
        description=f"For {amount} stars",
        prices=prices,
        provider_token="",
        payload=f"{amount}_stars",
        currency="XTR",
        reply_markup=kb.as_markup()
    )

@router.callback_query(F.data == "donate_cancel")
async def on_donate_cancel(callback: CallbackQuery):
    """
    Cancels the payment: closes the invoice message.
    """
    await callback.answer("Payment canceled.")
    await callback.message.delete()

@router.pre_checkout_query()
async def pre_checkout_query(query: PreCheckoutQuery):
    await query.answer(ok=True)

@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    t_id = message.successful_payment.telegram_payment_charge_id
    await message.answer(f"Payment successful! Transaction ID: {t_id}")


@router.message(Command("refund"))
async def cmd_refund(message: Message, bot: Bot, command: CommandObject):
    """
    Example command: /refund <transaction_id> for payment refund.
    """
    t_id = command.args
    if not t_id:
        await message.answer("Please provide a transaction ID for the refund.")
        return

    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=t_id
        )
        await message.answer("Refund processed successfully.")
    except TelegramBadRequest as e:
        if "CHARGE_ALREADY_REFUNDED" in e.message:
            await message.answer("This payment has already been refunded.")
        else:
            await message.answer("Could not find the payment or process the refund.")
