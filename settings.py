#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Bot Telegram untuk bermain UNO dalam obrolan grup
# Hak Cipta (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# Program ini adalah perangkat lunak bebas: Anda dapat mendistribusikan ulang dan/atau memodifikasi
# di bawah ketentuan Lisensi Umum GNU Affero yang diterbitkan oleh
# Free Software Foundation, baik versi 3 dari Lisensi, atau
# (sesuai pilihan Anda) versi yang lebih baru.
#
# Program ini didistribusikan dengan harapan bahwa ini akan berguna,
# tetapi TANPA GARANSI APA PUN; bahkan tanpa jaminan tersirat dari
# DIPERDAGANGKAN atau KECOCOKAN UNTUK TUJUAN TERTENTU. Lihat
# Lisensi Umum GNU Affero untuk detail lebih lanjut.
#
# Anda seharusnya telah menerima salinan Lisensi Umum GNU Affero
# bersama dengan program ini. Jika tidak, lihat <http://www.gnu.org/licenses/>.


from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import CommandHandler, Filters, MessageHandler, CallbackContext

from utils import send_async
from user_setting import UserSetting
from shared_vars import dispatcher
from locales import available_locales
from internationalization import _, user_locale


@user_locale
def show_settings(update: Update, context: CallbackContext):
    chat = update.message.chat

    if update.message.chat.type != 'private':
        send_async(context.bot, chat.id,
                   text=_("Silakan ubah pengaturan Anda di obrolan pribadi dengan "
                          "bot."))
        return

    us = UserSetting.get(id=update.message.from_user.id)

    if not us:
        us = UserSetting(id=update.message.from_user.id)

    if not us.stats:
        stats = '📊' + ' ' + _("Aktifkan statistik")
    else:
        stats = '❌' + ' ' + _("Hapus semua statistik")

    kb = [[stats], ['🌍' + ' ' + _("Bahasa")]]
    send_async(context.bot, chat.id, text='🔧' + ' ' + _("Pengaturan"),
               reply_markup=ReplyKeyboardMarkup(keyboard=kb,
                                                one_time_keyboard=True))


@user_locale
def kb_select(update: Update, context: CallbackContext):
    chat = update.message.chat
    user = update.message.from_user
    option = context.match[1]

    if option == '📊':
        us = UserSetting.get(id=user.id)
        us.stats = True
        send_async(context.bot, chat.id, text=_("Statistik diaktifkan!"))

    elif option == '🌍':
        kb = [[locale + ' - ' + descr]
              for locale, descr
              in sorted(available_locales.items())]
        send_async(context.bot, chat.id, text=_("Pilih bahasa"),
                   reply_markup=ReplyKeyboardMarkup(keyboard=kb,
                                                    one_time_keyboard=True))

    elif option == '❌':
        us = UserSetting.get(id=user.id)
        us.stats = False
        us.first_places = 0
        us.games_played = 0
        us.cards_played = 0
        send_async(context.bot, chat.id, text=_("Statistik dihapus dan dinonaktifkan!"))


@user_locale
def locale_select(update: Update, context: CallbackContext):
    chat = update.message.chat
    user = update.message.from_user
    option = context.match[1]

    if option in available_locales:
        us = UserSetting.get(id=user.id)
        us.lang = option
        _.push(option)
        send_async(context.bot, chat.id, text=_("Bahasa diatur!"))
        _.pop()

def register():
    dispatcher.add_handler(CommandHandler('settings', show_settings))
    dispatcher.add_handler(MessageHandler(Filters.regex('^([' + '📊' +
                                                        '🌍' +
                                                        '❌' + ']) .+$'),
                                        kb_select))
    dispatcher.add_handler(MessageHandler(Filters.regex(r'^(\w\w_\w\w) - .*'),
                                        locale_select))
