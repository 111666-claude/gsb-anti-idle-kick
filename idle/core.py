"""挂机踢出：按无操作时长给出 ok / warn / kick，白名单玩家永远例外。

缺陷：白名单不生效、到点判定用大于、没有宽限期直接踢、touch 事件不幂等、
每次判定全扫玩家表。
"""


class IdleGuard:
    """挂机判定台账。"""

    def __init__(self, idle_ms=1000, grace_ms=500):
        self.idle_ms = idle_ms
        self.grace_ms = grace_ms
        self.last = {}
        self.whitelist = set()
        self.handled = {}
        self.scanned = 0

    def allow(self, player):
        """把一个玩家放进白名单。"""
        self.whitelist.add(player)

    def touch(self, event_id, player, now_ms):
        """记录一次操作。缺陷：event_id 不去重、白名单与宽限都没用上。"""
        self.handled[event_id] = True
        self.last[player] = now_ms

    def check(self, player, now_ms):
        """返回 ok / warn / kick。缺陷：白名单不生效、用大于判定、没有宽限、全扫玩家表。"""
        self.scanned += len(self.last)
        last = self.last.get(player, 0)
        if now_ms - last > self.idle_ms:
            return "kick"
        return "ok"

    def scanned_count(self):
        return self.scanned
