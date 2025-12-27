import math
import time
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def humanbytes(size):
    if not size: return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'

def time_formatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
          ((str(hours) + "h, ") if hours else "") + \
          ((str(minutes) + "m, ") if minutes else "") + \
          ((str(seconds) + "s, ") if seconds else "")
    return tmp[:-2]

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if round(diff % 5.00) == 0 or current == total:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion
        
        progress = "[{0}{1}] \n".format(
            ''.join(["●" for i in range(math.floor(percentage / 5))]),
            ''.join(["○" for i in range(20 - math.floor(percentage / 5))])
        )
        
        tmp = progress + "**Done:** {0} of {1}\n**Speed:** {2}/s\n**ETA:** {3}".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            time_formatter(estimated_total_time) if estimated_total_time != '' else "0 s"
        )
        
        cancel_btn = InlineKeyboardMarkup([[InlineKeyboardButton("Cancel ❌", callback_data="cancel")]])
        
        try:
            await message.edit(text="{}\n{}".format(ud_type, tmp), reply_markup=cancel_btn)
        except:
            pass
