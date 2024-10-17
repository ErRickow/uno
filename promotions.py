"""
Promote other UNO bots
"""
import random


# Promotion messages and their weights
PROMOTIONS = {
    """
For a more modern UNO experience, <a href="https://t.me/uno9bot/uno">try out</a> the new <a href="https://t.me/uno9bot?start=ref-unobot">@uno9bot</a>.
""": 2.0,
    """
Also check out @UnoDemoBot, a newer version of this bot with exclusive modes and features!
""": 1.0,
    """
Discover @Erprembot for a smarter assistant to handle all your group needs and more! This bot is designed to help manage groups, offer utilities, and provide entertainment.
""": 1.5,
    """
Need help or want to discuss more? Join our support group at <a href="https://t.me/er_support_grou">@er_support_grou</a> where you can ask questions, get assistance, and talk about the latest bot features.
""": 1.5,
    """
Enjoy the classic UNO game experience with new features in @Erprembot and stay updated with the latest game modes!
""": 1.0,
}

def get_promotion():
    """ Get a random promotion message """
    return random.choices(list(PROMOTIONS.keys()), weights=list(PROMOTIONS.values()))[0]

def send_promotion(chat, chance=1.0):
    """ (Maybe) send a promotion message """
    if random.random() <= chance:
        chat.send_message(get_promotion(), parse_mode='HTML')


def send_promotion_async(chat, chance=1.0):
    """ Send a promotion message asynchronously """

    from utils import dispatcher, error
    try:
        dispatcher.run_async(send_promotion, chat, chance=chance)
    except Exception as e:
        error(None, None, e)
