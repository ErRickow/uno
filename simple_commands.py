#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Bot Telegram untuk bermain UNO di obrolan grup
# Copyright (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# Program ini adalah perangkat lunak bebas: Anda dapat mendistribusikan ulang dan/atau memodifikasinya
# di bawah ketentuan Lisensi Publik Umum Affero GNU seperti
# yang diterbitkan oleh Free Software Foundation, baik versi 3 dari Lisensi, atau
# (sesuai pilihan Anda) versi yang lebih baru.
#
# Program ini didistribusikan dengan harapan dapat berguna,
# tetapi TANPA GARANSI; tanpa bahkan jaminan tersirat tentang
# DIPERJUALBELIKAN atau KECOCOKAN UNTUK TUJUAN TERTENTU. Lihat
# Lisensi Publik Umum Affero GNU untuk lebih jelasnya.
#
# Anda seharusnya menerima salinan Lisensi Publik Umum Affero GNU
# bersama dengan program ini. Jika tidak, lihat <http://www.gnu.org/licenses/>.

from telegram import ParseMode, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackContext

from user_setting import UserSetting
from utils import send_async
from shared_vars import dispatcher
from internationalization import _, user_locale
from promotions import send_promotion

MUST_JOIN = ["Er_support_group", "ZeebSupport"]

async def must_join_channel(update: Update, context: CallbackContext):
    user = update.effective_user
    bot = context.bot

    if not MUST_JOIN:
        return

    for channel in MUST_JOIN:
        try:
            # Memeriksa apakah pengguna sudah menjadi anggota channel
            member = await bot.get_chat_member(channel, user.id)
        except:
            # Jika pengguna bukan anggota, beri tahu pengguna untuk bergabung
            await notify_user_must_join(update, context, channel, user)
            return

async def notify_user_must_join(update: Update, context: CallbackContext, channel, user):
    """Notifikasi pengguna untuk bergabung ke channel."""
    bot = context.bot

    # Membuat tautan undangan untuk channel
    if channel.isalpha():
        link = f"https://t.me/{channel}"
    else:
        chat_info = await bot.get_chat(channel)
        link = chat_info.invite_link

    try:
        # Mengirimkan pesan dan gambar notifikasi
        await update.message.reply_photo(
            photo="https://ibb.co.com/nbD5ZNk",
            caption=f"Untuk menggunakan bot ini, kamu harus bergabung dulu ke channel kami [di sini]({link}). Setelah bergabung, silakan ketik /start kembali.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔗 GABUNG SEKARANG", url=link),
                    ]
                ]
            ),
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error saat mengirim pesan: {e}")


@user_locale
def help_handler(update: Update, context: CallbackContext):
    """Handler untuk perintah /help"""
    help_text = _("<blockquote>"
      "Ikuti langkah-langkah ini:\n\n"
      "1. Tambahkan bot ini ke grup\n"
      "2. Di grup, mulai permainan baru dengan /new atau bergabung dengan permainan"
      " yang sedang berjalan dengan /join\n"
      "3. Setelah minimal dua pemain bergabung, mulai permainan dengan"
      " /start\n"
      "4. Ketik <code>@unobot</code> di kotak obrolan Anda dan tekan "
      "<b>spasi</b>, atau klik teks <code>via @unoanjengbot</code> "
      "di samping pesan. Anda akan melihat kartu Anda (beberapa berwarna abu-abu), "
      "opsi tambahan seperti menggambar, dan <b>?</b> untuk melihat "
      "status permainan saat ini. <b>Kartu yang berwarna abu-abu</b> adalah kartu yang "
      "<b>tidak bisa dimainkan</b> saat ini. Ketuk opsi untuk melaksanakan "
      "aksi yang dipilih.\n"
      "Pemain bisa bergabung dengan permainan kapan saja. Untuk keluar dari permainan,\n"
      "gunakan /leave. Jika pemain memakan waktu lebih dari 90 detik untuk bermain,\n"
      "Anda bisa menggunakan /skip untuk melewati pemain tersebut. Gunakan /notify_me untuk "
      "menerima pesan pribadi saat permainan baru dimulai.\n\n"
      "<b>Bahasa</b> dan pengaturan lainnya: /settings\n"
      "Perintah lainnya (hanya pencipta permainan):\n"
      "/close - Tutup lobi\n"
      "/open - Buka lobi\n"
      "/kill - Mengakhiri permainan\n"
      "/kick - Pilih pemain untuk dikeluarkan "
      "dengan membalas pesan pemain tersebut\n"
      "/enable_translations - Terjemahkan teks yang relevan ke semua "
      "bahasa yang digunakan dalam permainan\n"
      "/disable_translations - Gunakan bahasa Inggris untuk teks tersebut\n\n"
      "<b>Eksperimental:</b> Bermain di beberapa grup pada saat yang sama. "
      "Tekan tombol <code>Game saat ini: ...</code> dan pilih grup "
      "di mana Anda ingin memainkan kartu.\n"
      "Jika Anda menyukai bot ini, "
      "<a href=\"https://telegram.me/storebot?start=UnoAnjengBot\">"
      "beri peringkat</a>, bergabunglah dengan "
      "<a href=\"https://telegram.me/pamerdong\">saluran pembaruan</a>"
      " dan beli permainan kartu UNO."
      "</blockquote>")

    def _send():
      update.message.chat.send_message(
          help_text,
          parse_mode=ParseMode.HTML,
          disable_web_page_preview=True,
      )
      send_promotion(update.effective_chat)

    context.dispatcher.run_async(_send)

@user_locale
def modes(update: Update, context: CallbackContext):
    """Handler untuk perintah /help"""
    modes_explanation = _("<blockquote>Bot UNO ini memiliki empat mode permainan: Klasik, Sanic, Wild, dan Teks.</blockquote>\n\n"
      "<blockquote><pre> 🎻 Mode Klasik menggunakan dek UNO konvensional dan tidak ada auto skip.</pre>\n"
      "<pre> 🚀 Mode Sanic menggunakan dek UNO konvensional dan bot secara otomatis melewati pemain jika dia terlalu lama bermain.</pre>\n"
      "<pre> 🐉 Mode Wild menggunakan dek dengan lebih banyak kartu spesial, variasi angka yang lebih sedikit, dan tidak ada auto skip.</pre>\n"
      "<pre> ✍️ Mode Teks menggunakan dek UNO konvensional, tetapi alih-alih stiker, mode ini menggunakan teks.</pre></blockquote>\n\n"
      "<blockquote>Untuk mengubah mode permainan, PEMBUAT PERMAINAN harus mengetik nama panggilan bot dan spasi, "
      "seperti saat bermain kartu, dan semua opsi mode permainan akan muncul.</blockquote>")
    send_async(context.bot, update.message.chat_id, text=modes_explanation,
               parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@user_locale
def source(update: Update, context: CallbackContext):
    """Handler untuk perintah /help"""
    source_text = _("<blockquote>Bot ini dikembangkan oleh @chakszzz, seorang developer yang berdedikasi\n"
      "untuk menciptakan pengalaman permainan yang seru dan menyenangkan. \n"
      "Jika Anda memiliki saran, ingin berkontribusi, atau hanya ingin mengobrol, "
      "Anda bisa menghubungi langsung melalui Telegram.</blockquote>\n")

    attributions = _("Hubungi developer di Telegram: @chakszzz")

    send_async(context.bot, update.message.chat_id, text=source_text + '\n\n' +
                                                 attributions,
               parse_mode=ParseMode.HTML, disable_web_page_preview=True)

@user_locale
def news(update: Update, context: CallbackContext):
    """Handler untuk perintah /news"""
    send_async(context.bot, update.message.chat_id,
               text=_("Semua info di sini: https://telegram.me/Er_Support_Group"),
               disable_web_page_preview=True)

@user_locale
def stats(update: Update, context: CallbackContext):
    user = update.message.from_user
    us = UserSetting.get(id=user.id)
    if not us or not us.stats:
        send_async(context.bot, update.message.chat_id,
                   text=_("Anda belum mengaktifkan statistik. Gunakan /settings di "
                          "obrolan pribadi dengan bot untuk mengaktifkannya."))
    else:
        stats_text = list()

        n = us.games_played
        stats_text.append(
            _("{number} permainan dimainkan",
              "{number} permainan dimainkan",
              n).format(number=n)
        )

        n = us.first_places
        m = round((us.first_places / us.games_played) * 100) if us.games_played else 0
        stats_text.append(
            _("<blockquote>{number} juara pertama ({percent}%)</blockquote>",
              "<blockquote>{number} juara pertama ({percent}%)</blockquote>",
              n).format(number=n, percent=m)
        )

        n = us.cards_played
        stats_text.append(
            _("<blockquote>{number} kartu dimainkan</blockquote>",
              "<blockquote>{number} kartu dimainkan</blockquote>",
              n).format(number=n)
        )

        send_async(context.bot, update.message.chat_id,
                   text='\n'.join(stats_text))


def register():
    dispatcher.add_handler(CommandHandler('help', help_handler))
    dispatcher.add_handler(CommandHandler('info', source))
    dispatcher.add_handler(CommandHandler('news', news))
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('mode', modes))
