"""
Tool Name: Azure Activity Log Axe
Script Name: ascii_logo.py
Author: Nathan Eades
Date: 2024-06-01
Description: Controls ascii art output.
License: Apache License
"""

#   This file is part of Azure Activity Log Axe.
#
#   Copyright 2024 Permiso Security <https://permiso.io>
#         Nathan Eades:
#             - LinkedIn: <@eadesclouddef>
#             - GitHub: <eadesclouddef> or <neades2305>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from colorama import Fore, Style, init


def print_ascii_art():
    init()

    title = """
     A    ZZZZZ U   U RRRR  EEEEE       A     CCCCC TTTTT IIIII V   V IIIII TTTTT  Y   Y    L     OOO  GGGG        A    X   X EEEEE
    A A      Z  U   U R   R E          A A    C       T     I   V   V   I     T     Y Y     L    O   O G          A A    X X  E
   AaaaA    Z   U   U RRR   Eee       AaaaA   C       T     I   V   V   I     T      Y      L    O   O G  GG     AaaaA    X   Eee
  A     A  Z    U   U R  R  E        A     A  C       T     I    V V    I     T      Y      L    O   O G   G    A     A  X X  E
  A     A ZZZZZ  UUU  R   R EEEEE    A     A  CCCCC   T   IIIII   V   IIIII   T      Y      LLLL  OOO  GGGG     A     A X   X EEEEE
  """

    axe_key = (
        Fore.YELLOW + r"""
                       -------
                     /         \
                   /   / --- \   \
                 /    /       \    \
               /    /           \    \
             /    /               \    \
      """ +
        Fore.YELLOW + r"      |    /                 \    ---                                                           " + Fore.CYAN + "__________\n" +
        Fore.YELLOW + r"           /   _|                    |-     |                                                        " + Fore.CYAN + "/   |      |\n" +
        Fore.YELLOW + r"           -   /_______________________\    " + Fore.LIGHTRED_EX + r"--------------------------------------------------------" + Fore.CYAN + r"/" + Fore.YELLOW + r"-----------" + Fore.CYAN + "|\n" +
        Fore.YELLOW + r"         |                                                                                         " + Fore.YELLOW + r"/             \ " + "\n" +
        Fore.YELLOW + r"         |     ________________________                                                            " + Fore.YELLOW + r"\             /" + "\n" +
        Fore.YELLOW + r"           -   \                       /    " + Fore.LIGHTRED_EX + r"-------------------------------------------------------" + Fore.CYAN + r"/" + Fore.YELLOW + r"-------------" + Fore.CYAN + r"\ " + "\n" +
        Fore.YELLOW + r"           \   -|                    |-     |                                                      " + Fore.CYAN + "|    |         \\\n" +
        Fore.YELLOW + r"            |    \                 /    ---                                                        " + Fore.CYAN + "|    |         \\\n" +
        Fore.YELLOW + r"             \    \               /    /                                                           " + Fore.CYAN + "/    |          \\\n" +
        Fore.YELLOW + r"               \    \           /    /                                                            " + Fore.CYAN + r"/     " + Fore.WHITE + "|__________\\\n" +
        Fore.YELLOW + r"                 \    \       /    /                                                             " + Fore.CYAN + r"/     " + Fore.WHITE + "/            \\\n" +
        Fore.YELLOW + r"                   \   \ --- /   /                                                              " + Fore.CYAN + r"/    " + Fore.WHITE + "/               \\\n" +
        Fore.YELLOW + r"                     \         /                                                               " + Fore.CYAN + r"/   " + Fore.WHITE + "/                  \\\n" +
        Fore.YELLOW + r"                       -------                                                                " + Fore.CYAN + r"/  " + Fore.WHITE + "/                     \\\n" +
        Fore.CYAN + r"                                                                                             / " + Fore.WHITE + r"/ ____            _\_\   \ " + "\n" +
        Fore.WHITE + r"                                                                                            //__/    \ -------- /    \___\ " +
        Style.RESET_ALL
    )

    from_permiso = r"""
         __  ___ __     . __   __     __  __             __  __
        |__)|__ |__)|\/||/__` /  \   |__)/ /\   |    /\ |__)/__`
  FROM: |   |___|  \|  ||.__/ \__/   |   \/_/   |___/~~\|__).__/
  """

    print(
        title +
        "" +
        axe_key +
        "" +
        from_permiso +
        "\n" +
        "  Authored By: Nathan Eades  (EadesCloudDef)" +
        "\n\n\n"
    )

    Style.RESET_ALL
