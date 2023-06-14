from enum import IntEnum


class ProgramType(IntEnum):
    paid = 0
    free_promo = 1
    paid_promo = 2
    event = 3


class Actions(IntEnum):
    registered = 0
    cancelled = 1
    restored = 2
    visit_marked = 3
    visit_reset = 4


class PaymentMethod(IntEnum):
    offline_cash = 1
    offline_card = 2
    online = 3
    terminal = 4
    bank = 5
    inner_transfer = 6
    natural_service = 7
    documented_service = 8
    offline_fast_payment_system = 9


class RecordStatus(IntEnum):
    not_came_free_promo = 1
    came_free_promo = 2
    marked_regular = 3
    registered = 4
    restored = 5
    not_came_paid_promo = 6
    came_paid_promo = 7
    cancelled_regular = 8
    cancelled_paid_promo = 9
    cancelled_free_promo = 10
    came_event = 11


class LeadFunnels(IntEnum):
    primary = 1
    secondary = 2


class DealAction(IntEnum):
    visits = 1
    buys = 2
    bought = 3


class WordPressForm(IntEnum):
    sign_up_for_lesson = 371
    sign_up_for_lesson_bottom = 5716
    sign_up_for_vocal_lesson = 2169
    sign_up_for_vocal_lesson_bottom = 2167
    sign_up_for_promo_lesson = 2168
    promo_lesson = 220
    promo_lesson_bottom = 3886
    home = 2170
    blocked_home = 2167


class CustomerNotificationMedium(IntEnum):
    Email = 0
    Sms = 1
    Telegram = 2
    WhatsApp = 3

