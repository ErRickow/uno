#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Telegram bot to play UNO in group chats
# Copyright (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
from datetime import datetime

from telegram import ParseMode, InlineKeyboardMarkup, \
    InlineKeyboardButton, Update
from telegram.ext import InlineQueryHandler, ChosenInlineResultHandler, \
    CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from telegram.ext.dispatcher import run_async

import card as c
import settings
import simple_commands
from actions import do_skip, do_play_card, do_draw, do_call_bluff, start_player_countdown
from config import WAITING_TIME, DEFAULT_GAMEMODE, MIN_PLAYERS
from errors import (NoGameInChatError, LobbyClosedError, AlreadyJoinedError,
                    NotEnoughPlayersError, DeckEmptyError)
from internationalization import _, __, user_locale, game_locales
from results import (add_call_bluff, add_choose_color, add_draw, add_gameinfo,
                     add_no_game, add_not_started, add_other_cards, add_pass,
                     add_card, add_mode_classic, add_mode_fast, add_mode_wild, add_mode_text)
from shared_vars import gm, updater, dispatcher
from simple_commands import help_handler
from start_bot import start_bot
from utils import display_name
from utils import send_async, answer_async, error, TIMEOUT, user_is_creator_or_admin, user_is_creator, game_is_running


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

@user_locale
def notify_me(update: Update, context: CallbackContext):
    """Handler for /notify_me command, pm people for next game"""
    chat_id = update.message.chat_id
    if update.message.chat.type == 'private':
        send_async(bot,
                   chat_id,
                   text=_("Send this command in a group to be notified "
                          "when a new game is started there."))
    else:
        try:
            gm.remind_dict[chat_id].add(update.message.from_user.id)
        except KeyError:
            gm.remind_dict[chat_id] = {update.message.from_user.id}


@user_locale
def new_game(update: Update, context: CallbackContext):
    """Handler for the /new command"""
    chat_id = update.message.chat_id

    if update.message.chat.type == 'private':
        help_handler(update, context)

    else:

        if update.message.chat_id in gm.remind_dict:
            for user in gm.remind_dict[update.message.chat_id]:
                send_async(context.bot,
                           user,
                           text=_("Game baru dimulai di {title}").format(
                                title=update.message.chat.title))

            del gm.remind_dict[update.message.chat_id]

        game = gm.new_game(update.message.chat)
        game.starter = update.message.from_user
        game.owner.append(update.message.from_user.id)
        game.mode = DEFAULT_GAMEMODE
        send_async(context.bot, chat_id,
                   text=_("Membuat game baru! Gabung gamenya dengan ketik /join "
                          "dan start gamenya ketik /start"))


@user_locale
def kill_game(update: Update, context: CallbackContext):
    """Handler untuk perintah /kill"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    if not games:
            send_async(context.bot, chat.id,
                       text=_("Tidak ada permainan yang berjalan di obrolan ini."))
            return

    game = games[-1]

    if user_is_creator_or_admin(user, game, context.bot, chat):

        try:
            gm.end_game(chat, user)
            send_async(context.bot, chat.id, text=__("Permainan Selesai!", multi=game.translate))

        except NoGameInChatError:
            send_async(context.bot, chat.id,
                       text=_("Permainan belum dimulai. "
                              "Ikut permainan dengan /join dan mulai permainan dengan /start"),
                       reply_to_message_id=update.message.message_id)

    else:
        send_async(context.bot, chat.id,
                  text=_("Hanya pembuat permainan ({name}) dan admin yang bisa melakukan itu.")
                  .format(name=game.starter.first_name),
                  reply_to_message_id=update.message.message_id)

@user_locale
def join_game(update: Update, context: CallbackContext):
    """Handler untuk perintah /join"""
    chat = update.message.chat

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    try:
        gm.join_game(update.message.from_user, chat)

    except LobbyClosedError:
            send_async(context.bot, chat.id, text=_("Lobi telah ditutup"))

    except NoGameInChatError:
        send_async(context.bot, chat.id,
                   text=_("Tidak ada permainan yang berjalan saat ini. "
                          "Buat permainan baru dengan /new"),
                   reply_to_message_id=update.message.message_id)

    except AlreadyJoinedError:
        send_async(context.bot, chat.id,
                   text=_("Kamu sudah bergabung dalam permainan. Mulai permainan "
                          "dengan /start"),
                   reply_to_message_id=update.message.message_id)

    except DeckEmptyError:
        send_async(context.bot, chat.id,
                   text=_("Tidak cukup kartu yang tersisa di dek untuk "
                          "pemain baru bergabung."),
                   reply_to_message_id=update.message.message_id)

    else:
        send_async(context.bot, chat.id,
                   text=_("Bergabung dengan permainan"),
                   reply_to_message_id=update.message.message_id)


@user_locale
def leave_game(update: Update, context: CallbackContext):
    """Handler untuk perintah /leave"""
    chat = update.message.chat
    user = update.message.from_user

    player = gm.player_for_user_in_chat(user, chat)

    if player is None:
        send_async(context.bot, chat.id, text=_("Kamu tidak sedang bermain dalam permainan di "
                                        "grup ini."),
                   reply_to_message_id=update.message.message_id)
        return

    game = player.game
    user = update.message.from_user

    try:
        gm.leave_game(user, chat)

    except NoGameInChatError:
        send_async(context.bot, chat.id, text=_("Kamu tidak sedang bermain dalam permainan di "
                                        "grup ini."),
                   reply_to_message_id=update.message.message_id)

    except NotEnoughPlayersError:
        gm.end_game(chat, user)
        send_async(context.bot, chat.id, text=__("Permainan berakhir!", multi=game.translate))

    else:
        if game sudah dimulai:
            send_async(context.bot, chat.id,
                       text=__("Oke. Pemain Berikutnya: {name}",
                               multi=game.translate).format(
                           name=display_name(game.current_player.user)),
                       reply_to_message_id=update.message.message_id)
        else:
            send_async(context.bot, chat.id,
                       text=__("{name} keluar dari permainan sebelum dimulai.",
                               multi=game.translate).format(
                           name=display_name(user)),
                       reply_to_message_id=update.message.message_id)


@user_locale
def kick_player(update: Update, context: CallbackContext):
    """Handler untuk perintah /kick"""

    if update.message.chat.type == 'private':
        help_handler(update, context)
        return

    chat = update.message.chat
    user = update.message.from_user

    try:
        game = gm.chatid_games[chat.id][-1]

    except (KeyError, IndexError):
            send_async(context.bot, chat.id,
                   text=_("Tidak ada permainan yang berjalan saat ini. "
                          "Buat permainan baru dengan /new"),
                   reply_to_message_id=update.message.message_id)
            return

    if not game.started:
        send_async(context.bot, chat.id,
                   text=_("Permainan belum dimulai. "
                          "Bergabunglah dengan /join dan mulai permainan dengan /start"),
                   reply_to_message_id=update.message.message_id)
        return

    if user_is_creator_or_admin(user, game, context.bot, chat):

        if update.message.reply_to_message:
            kicked = update.message.reply_to_message.from_user

            try:
                gm.leave_game(kicked, chat)

            except NoGameInChatError:
                send_async(context.bot, chat.id, text=_("Pemain {name} tidak ditemukan dalam permainan saat ini.".format(name=display_name(kicked))),
                                reply_to_message_id=update.message.message_id)
                return

            except NotEnoughPlayersError:
                gm.end_game(chat, user)
                send_async(context.bot, chat.id,
                                text=_("{0} dikeluarkan oleh {1}".format(display_name(kicked), display_name(user))))
                send_async(context.bot, chat.id, text=__("Permainan berakhir!", multi=game.translate))
                return

            send_async(context.bot, chat.id,
                            text=_("{0} dikeluarkan oleh {1}".format(display_name(kicked), display_name(user))))

        else:
            send_async(context.bot, chat.id,
                text=_("Silakan balas pesan dari orang yang ingin Anda keluarkan dan ketik /kick lagi."),
                reply_to_message_id=update.message.message_id)
            return

        send_async(context.bot, chat.id,
                   text=__("Oke. Pemain Berikutnya: {name}",
                           multi=game.translate).format(
                       name=display_name(game.current_player.user)),
                   reply_to_message_id=update.message.message_id)

    else:
        send_async(context.bot, chat.id,
                  text=_("Hanya pembuat permainan ({name}) dan admin yang bisa melakukan itu.")
                  .format(name=game.starter.first_name),
                  reply_to_message_id=update.message.message_id)


def select_game(update: Update, context: CallbackContext):
    """Handler untuk callback query dalam memilih permainan saat ini"""

    chat_id = int(update.callback_query.data)
    user_id = update.callback_query.from_user.id
    players = gm.userid_players[user_id]
    for player in players:
        if player.game.chat.id == chat_id:
            gm.userid_current[user_id] = player
            break
    else:
        send_async(bot,
                   update.callback_query.message.chat_id,
                   text=_("Permainan tidak ditemukan."))
        return

    def selected():
        back = [[InlineKeyboardButton(text=_("Kembali ke grup terakhir"),
                                      switch_inline_query='')]]
        context.bot.answerCallbackQuery(update.callback_query.id,
                                text=_("Silakan beralih ke grup yang Anda pilih!"),
                                show_alert=False,
                                timeout=TIMEOUT)

        context.bot.editMessageText(chat_id=update.callback_query.message.chat_id,
                            message_id=update.callback_query.message.message_id,
                            text=_("Grup yang dipilih: {group}\n"
                                   "<b>Pastikan Anda beralih ke grup yang benar!</b>").format(
                                group=gm.userid_current[user_id].game.chat.title),
                            reply_markup=InlineKeyboardMarkup(back),
                            parse_mode=ParseMode.HTML,
                            timeout=TIMEOUT)

    dispatcher.run_async(selected)


@game_locales
def status_update(update: Update, context: CallbackContext):
    """Menghapus pemain dari permainan jika pengguna meninggalkan grup"""
    chat = update.message.chat

    if update.message.left_chat_member:
        user = update.message.left_chat_member

        try:
            gm.leave_game(user, chat)
            game = gm.player_for_user_in_chat(user, chat).game

        except NoGameInChatError:
            pass
        except NotEnoughPlayersError:
            gm.end_game(chat, user)
            send_async(context.bot, chat.id, text=__("Permainan berakhir!",
                                             multi=game.translate))
        else:
            send_async(context.bot, chat.id, text=__("Menghapus {name} dari permainan",
                                             multi=game.translate)
                       .format(name=display_name(user)))


@game_locales
@user_locale
def start_game(update: Update, context: CallbackContext):
    """Handler untuk perintah /start"""

    if update.message.chat.type != 'private':
        chat = update.message.chat

        try:
            game = gm.chatid_games[chat.id][-1]
        except (KeyError, IndexError):
            send_async(context.bot, chat.id,
                       text=_("Tidak ada permainan yang berjalan di obrolan ini. Buat "
                              "yang baru dengan /new"))
            return

        if game.started:
            send_async(context.bot, chat.id, text=_("Permainan sudah dimulai"))

        elif len(game.players) < MIN_PLAYERS:
            send_async(context.bot, chat.id,
                       text=__("Setidaknya {minplayers} pemain harus /join permainan "
                              "sebelum Anda bisa memulainya").format(minplayers=MIN_PLAYERS))

        else:
            # Memulai permainan
            game.start()

            for player in game.players:
                player.draw_first_hand()
            choice = [[InlineKeyboardButton(text=_("Buat pilihanmu!"), switch_inline_query_current_chat='')]]
            first_message = (
                __("Pemain pertama: {name}\n"
                   "Gunakan /close untuk menghentikan orang dari bergabung ke permainan.\n"
                   "Aktifkan multi-terjemahan dengan /enable_translations",
                   multi=game.translate)
                .format(name=display_name(game.current_player.user)))

            def send_first():
                """Kirim kartu pertama dan pemain pertama"""

                context.bot.sendSticker(chat.id,
                                sticker=c.STICKERS[str(game.last_card)],
                                timeout=TIMEOUT)

                context.bot.sendMessage(chat.id,
                                text=first_message,
                                reply_markup=InlineKeyboardMarkup(choice),
                                timeout=TIMEOUT)

            dispatcher.run_async(send_first)
            start_player_countdown(context.bot, game, context.job_queue)

    elif len(context.args) and context.args[0] == 'select':
        players = gm.userid_players[update.message.from_user.id]

        groups = list()
        for player in players:
            title = player.game.chat.title

            if player == gm.userid_current[update.message.from_user.id]:
                title = '- %s -' % player.game.chat.title

            groups.append(
                [InlineKeyboardButton(text=title,
                                      callback_data=str(player.game.chat.id))]
            )

        send_async(context.bot, update.message.chat_id,
                   text=_('Silakan pilih grup yang ingin Anda mainkan.'),
                   reply_markup=InlineKeyboardMarkup(groups))

    else:
        help_handler(update, context)


@user_locale
def close_game(update: Update, context: CallbackContext):
    """Handler untuk perintah /close"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=_("Tidak ada permainan yang berjalan di obrolan ini."))
        return

    game = games[-1]

    if user.id in game.owner:
        game.open = False
        send_async(context.bot, chat.id, text=_("Menutup lobi. "
                                        "Tidak ada pemain yang bisa bergabung ke permainan ini."))
        return

    else:
        send_async(context.bot, chat.id,
                   text=_("Hanya pembuat permainan ({name}) dan admin yang bisa melakukan itu.")
                   .format(name=game.starter.first_name),
                   reply_to_message_id=update.message.message_id)
        return


@user_locale
def open_game(update: Update, context: CallbackContext):
    """Handler untuk perintah /open"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=_("Tidak ada permainan yang berjalan di obrolan ini."))
        return

    game = games[-1]

    if user.id in game.owner:
        game.open = True
        send_async(context.bot, chat.id, text=_("Membuka lobi. "
                                        "Pemain baru dapat /join permainan."))
        return
    else:
        send_async(context.bot, chat.id,
                   text=_("Hanya pembuat permainan ({name}) dan admin yang bisa melakukan itu.")
                   .format(name=game.starter.first_name),
                   reply_to_message_id=update.message.message_id)
        return


@user_locale
def enable_translations(update: Update, context: CallbackContext):
    """Handler untuk perintah /enable_translations"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=_("Tidak ada permainan yang berjalan di obrolan ini."))
        return

    game = games[-1]

    if user.id in game.owner:
        game.translate = True
        send_async(context.bot, chat.id, text=_("Multi-terjemahan diaktifkan. "
                                        "Nonaktifkan dengan /disable_translations"))
        return

    else:
        send_async(context.bot, chat.id,
                   text=_("Hanya pembuat permainan ({name}) dan admin yang bisa melakukan itu.")
                   .format(name=game.starter.first_name),
                   reply_to_message_id=update.message.message_id)
        return


@user_locale
def disable_translations(update: Update, context: CallbackContext):
    """Handler untuk perintah /disable_translations"""
    chat = update.message.chat
    user = update.message.from_user
    games = gm.chatid_games.get(chat.id)

    if not games:
        send_async(context.bot, chat.id,
                   text=_("Tidak ada permainan yang berjalan di obrolan ini."))
        return

    game = games[-1]

    if user.id in game.owner:
        game.translate = False
        send_async(context.bot, chat.id, text=_("Multi-terjemahan dinonaktifkan. "
                                        "Aktifkan lagi dengan "
                                        "/enable_translations"))
        return

    else:
        send_async(context.bot, chat.id,
                   text=_("Hanya pembuat permainan ({name}) dan admin yang bisa melakukan itu.")
                   .format(name=game.starter.first_name),
                   reply_to_message_id=update.message.message_id)
        return


@game_locales
@user_locale
def skip_player(update: Update, context: CallbackContext):
    """Handler untuk perintah /skip"""
    chat = update.message.chat
    user = update.message.from_user

    player = gm.player_for_user_in_chat(user, chat)
    if not player:
        send_async(context.bot, chat.id,
                   text=_("Anda tidak sedang bermain dalam permainan di obrolan ini."))
        return

    game = player.game
    skipped_player = game.current_player

    started = skipped_player.turn_started
    now = datetime.now()
    delta = (now - started).seconds

    # Anda tidak bisa melewati jika pemain saat ini masih memiliki waktu tersisa
    # Anda bisa melewati diri sendiri meskipun Anda memiliki waktu tersisa (Anda tetap akan menggambar)
    if delta < skipped_player.waiting_time and player != skipped_player:
        n = skipped_player.waiting_time - delta
        send_async(context.bot, chat.id,
                   text=_("Silakan tunggu {time} detik",
                          "Silakan tunggu {time} detik",
                          n)
                   .format(time=n),
                   reply_to_message_id=update.message.message_id)
    else:
        do_skip(context.bot, player)


@game_locales
@user_locale
def reply_to_query(update: Update, context: CallbackContext):
    """
    Handler untuk kueri inline.
    Membangun daftar hasil untuk kueri inline dan menjawab klien.
    """
    results = list()
    switch = None

    try:
        user = update.inline_query.from_user
        user_id = user.id
        players = gm.userid_players[user_id]
        player = gm.userid_current[user_id]
        game = player.game
    except KeyError:
        add_no_game(results)
    else:

        # Permainan belum dimulai.
        # Pembuat dapat mengubah mode permainan, pengguna lain hanya mendapatkan pesan "permainan belum dimulai".
        if not game.started:
            if user_is_creator(user, game):
                add_mode_classic(results)
                add_mode_fast(results)
                add_mode_wild(results)
                add_mode_text(results)
            else:
                add_not_started(results)


        elif user_id == game.current_player.user.id:
            if game.choosing_color:
                add_choose_color(results, game)
                add_other_cards(player, results, game)
            else:
                if not player.drew:
                    add_draw(player, results)

                else:
                    add_pass(results, game)

                if game.last_card.special == c.DRAW_FOUR and game.draw_counter:
                    add_call_bluff(results, game)

                playable = player.playable_cards()
                added_ids = list()  # Duplikat tidak diperbolehkan

                for card in sorted(player.cards):
                    add_card(game, card, results,
                             can_play=(card in playable and
                                            str(card) not in added_ids))
                    added_ids.append(str(card))

                add_gameinfo(game, results)

        elif user_id != game.current_player.user.id or not game.started:
            for card in sorted(player.cards):
                add_card(game, card, results, can_play=False)

        else:
            add_gameinfo(game, results)

        for result in results:
            result.id += ':%d' % player.anti_cheat

        if players and game and len(players) > 1:
            switch = _('Permainan saat ini: {game}').format(game=game.chat.title)

    answer_async(context.bot, update.inline_query.id, results, cache_time=0,
                 switch_pm_text=switch, switch_pm_parameter='select')


@game_locales
@user_locale
def process_result(update: Update, context: CallbackContext):
    """
    Handler untuk hasil inline yang dipilih.
    Memeriksa tindakan pemain dan bertindak sesuai.
    """
    try:
        user = update.chosen_inline_result.from_user
        player = gm.userid_current[user.id]
        game = player.game
        result_id = update.chosen_inline_result.result_id
        chat = game.chat
    except (KeyError, AttributeError):
        return

    logger.debug("Hasil yang dipilih: " + result_id)

    result_id, anti_cheat = result_id.split(':')
    last_anti_cheat = player.anti_cheat
    player.anti_cheat += 1

    if result_id in ('hand', 'gameinfo', 'nogame'):
        return
    elif result_id.startswith('mode_'):
        # Lima karakter pertama adalah 'mode_', sisanya adalah mode permainan.
        mode = result_id[5:]
        game.set_mode(mode)
        logger.info("Mode permainan diubah menjadi {mode}".format(mode=mode))
        send_async(context.bot, chat.id, text=__("Mode permainan diubah menjadi {mode}".format(mode=mode)))
        return
    elif len(result_id) == 36:  # UUID hasil
        return
    elif int(anti_cheat) != last_anti_cheat:
        send_async(context.bot, chat.id,
                   text=__("Upaya curang oleh {name}", multi=game.translate)
                   .format(name=display_name(player.user)))
        return
    elif result_id == 'call_bluff':
        reset_waiting_time(context.bot, player)
        do_call_bluff(context.bot, player)
    elif result_id == 'draw':
        reset_waiting_time(context.bot, player)
        do_draw(context.bot, player)
    elif result_id == 'pass':
        game.turn()
    elif result_id in c.COLORS:
        game.choose_color(result_id)
    else:
        reset_waiting_time(context.bot, player)
        do_play_card(context.bot, player, result_id)

    if game_is_running(game):
        nextplayer_message = (
            __("Pemain berikutnya: {name}", multi=game.translate)
            .format(name=display_name(game.current_player.user)))
        choice = [[InlineKeyboardButton(text=_("Buat pilihanmu!"), switch_inline_query_current_chat='')]]
        send_async(context.bot, chat.id,
                        text=nextplayer_message,
                        reply_markup=InlineKeyboardMarkup(choice))
        start_player_countdown(context.bot, game, context.job_queue)


def reset_waiting_time(bot, player):
    """Mengatur ulang waktu tunggu untuk pemain dan mengirim pemberitahuan ke grup"""
    chat = player.game.chat

    if player.waiting_time < WAITING_TIME:
        player.waiting_time = WAITING_TIME
        send_async(bot, chat.id,
                   text=__("Waktu tunggu untuk {name} telah direset ke {time} "
                           "detik", multi=player.game.translate)
                   .format(name=display_name(player.user), time=WAITING_TIME))

# Add all handlers to the dispatcher and run the bot
dispatcher.add_handler(InlineQueryHandler(reply_to_query))
dispatcher.add_handler(ChosenInlineResultHandler(process_result, pass_job_queue=True))
dispatcher.add_handler(CallbackQueryHandler(select_game))
dispatcher.add_handler(CommandHandler('start', start_game, pass_args=True, pass_job_queue=True))
dispatcher.add_handler(CommandHandler('new', new_game))
dispatcher.add_handler(CommandHandler('kill', kill_game))
dispatcher.add_handler(CommandHandler('join', join_game))
dispatcher.add_handler(CommandHandler('leave', leave_game))
dispatcher.add_handler(CommandHandler('kick', kick_player))
dispatcher.add_handler(CommandHandler('open', open_game))
dispatcher.add_handler(CommandHandler('close', close_game))
dispatcher.add_handler(CommandHandler('enable_translations',
                                      enable_translations))
dispatcher.add_handler(CommandHandler('disable_translations',
                                      disable_translations))
dispatcher.add_handler(CommandHandler('skip', skip_player))
dispatcher.add_handler(CommandHandler('notify_me', notify_me))
simple_commands.register()
settings.register()
dispatcher.add_handler(MessageHandler(Filters.status_update, status_update))
dispatcher.add_error_handler(error)

start_bot(updater)
updater.idle()
