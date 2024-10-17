"""
Promote other UNO bots
"""
import random


# Promotion messages and their weights
PROMOTIONS = {
    """
<blockquote>
🚀 Also check out @erprembot, a powerful bot that allows you to create userbots for easy broadcasting in your groups! 🚀
<br>
🚀 Juga, lihat @erprembot, bot hebat yang memungkinkan Anda membuat userbot untuk siaran mudah di grup Anda! 🚀
</blockquote>
""": 1.0,
    """
<blockquote>
🎉 Join our support group at <a href="https://t.me/er_support_group">Support</a> to ask questions, get assistance, and discuss the latest bot features! Your community is here to help! 🎉
<br>
🎉 Bergabunglah dengan grup dukungan kami di <a href="https://t.me/er_support_group">Dukungan</a> untuk bertanya, mendapatkan bantuan, dan mendiskusikan fitur bot terbaru! Komunitas Anda ada di sini untuk membantu! 🎉
</blockquote>
""": 1.5,
    """
<blockquote>
🃏 Enjoy the classic UNO game experience with new features in @Pamerdong! Stay updated with the latest game modes and have endless fun with friends! 🃏
<br>
🃏 Nikmati pengalaman permainan UNO klasik dengan fitur baru di @Pamerdong! Tetap terupdate dengan mode permainan terbaru dan nikmati keseruan tanpa batas bersama teman! 🃏
</blockquote>
""": 1.0,
    """
<blockquote>
🤖 Discover @ChatWLayla, your friendly Telegram chatbot! Engage in fun conversations right in your group, share jokes, ask questions, and enjoy interactive features that will keep your community entertained! Let's chat! 🤖
<br>
🤖 Temukan @ChatWLayla, chatbot Telegram yang ramah! Ajak ngobrol dalam percakapan menyenangkan di grup Anda, bagikan lelucon, ajukan pertanyaan, dan nikmati fitur interaktif yang akan membuat komunitas Anda terhibur! Mari kita ngobrol! 🤖
</blockquote>
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
