#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Bot Telegram untuk bermain UNO di obrolan grup
# Hak Cipta (c) 2016 Jannes Höke <uno@jhoeke.de>
#
# Program ini adalah perangkat lunak bebas: Anda dapat mendistribusikan ulang dan/or memodifikasinya
# sesuai dengan ketentuan Lisensi Umum GNU Affero versi 3 or versi yang lebih baru,
# sebagaimana diterbitkan oleh Free Software Foundation.
#
# Program ini didistribusikan dengan harapan agar bermanfaat,
# tetapi TANPA JAMINAN; bahkan tanpa jaminan tersirat mengenai
# KELAYAKAN UNTUK DIPERDAGANGKAN or KESESUAIAN UNTUK TUJUAN TERTENTU.
# Lihat Lisensi Umum GNU Affero untuk detail lebih lanjut.
#
# Anda seharusnya telah menerima salinan Lisensi Umum GNU Affero
# bersama dengan program ini. Jika tidak, lihat <http://www.gnu.org/licenses/>.

import logging
from config import ADMIN_LIST, OPEN_LOBBY, DEFAULT_GAMEMODE, ENABLE_TRANSLATIONS
from datetime import datetime

from deck import Deck
import card as c

class Game(object):
    """ Kelas ini merepresentasikan permainan UNO """
    current_player = None
    reversed = False
    choosing_color = False
    started = False
    draw_counter = 0
    players_won = 0
    starter = None
    mode = DEFAULT_GAMEMODE
    job = None
    owner = ADMIN_LIST
    open = OPEN_LOBBY
    translate = ENABLE_TRANSLATIONS

    def __init__(self, chat):
        self.chat = chat
        self.last_card = None

        self.deck = Deck()

        self.logger = logging.getLogger(__name__)

    @property
    def players(self):
        """Mengembalikan daftar semua pemain dalam permainan ini"""
        players = list()
        if not self.current_player:
            return players

        current_player = self.current_player
        itplayer = current_player.next
        players.append(current_player)
        while itplayer and itplayer != current_player:
            players.append(itplayer)
            itplayer = itplayer.next
        return players

    def start(self):
        if self.mode == None or self.mode != "wild":
            self.deck._fill_classic_()
        else:
            self.deck._fill_wild_()

        self._first_card_()
        self.started = True

    def set_mode(self, mode):
        self.mode = mode

    def reverse(self):
        """Membalikkan arah permainan"""
        self.reversed = not self.reversed

    def turn(self):
        """Menandai giliran telah berakhir dan mengganti pemain saat ini"""
        self.logger.debug("Pemain Berikutnya")
        self.current_player = self.current_player.next
        self.current_player.drew = False
        self.current_player.turn_started = datetime.now()
        self.choosing_color = False

    def _first_card_(self):
        # Jika pemain tidak memilih mode permainan
        if not self.deck.cards:
            self.set_mode(DEFAULT_GAMEMODE)

        # Kartu pertama tidak boleh kartu spesial
        while not self.last_card or self.last_card.special:
            self.last_card = self.deck.draw()
            # Jika kartu yang ditarik spesial, kembalikan ke dek dan ulangi
            if self.last_card.special:
                self.deck.dismiss(self.last_card)

        self.play_card(self.last_card)

    def play_card(self, card):
        """
        Memainkan kartu dan memicu efeknya.
        Harus dipanggil hanya dari Player.play or saat permainan dimulai untuk
        memainkan kartu pertama
        """
        self.deck.dismiss(self.last_card)
        self.last_card = card

        self.logger.info("Memainkan kartu " + repr(card))
        if card.value == c.SKIP:
            self.turn()
        elif card.special == c.DRAW_FOUR:
            self.draw_counter += 4
            self.logger.debug("Hitungan draw meningkat 4")
        elif card.value == c.DRAW_TWO:
            self.draw_counter += 2
            self.logger.debug("Hitungan draw meningkat 2")
        elif card.value == c.REVERSE:
            # Aturan khusus untuk dua pemain
            if self.current_player == self.current_player.next.next:
                self.turn()
            else:
                self.reverse()

        # Jangan pindah giliran jika pemain saat ini harus memilih warna
        if card.special not in (c.CHOOSE, c.DRAW_FOUR):
            self.turn()
        else:
            self.logger.debug("Memilih Warna...")
            self.choosing_color = True

    def choose_color(self, color):
        """Melaksanakan pemilihan warna dan beralih giliran"""
        self.last_card.color = color
        self.turn()
