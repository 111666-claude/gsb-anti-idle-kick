"""挂机踢出：按无操作时长给出 ok / warn / kick，白名单玩家永远例外。"""


class IdleGuard:
    """挂机判定台账。

    判定只依赖最近一次生效操作的时刻，与 ``check`` 的调用历史无关：
    无记录按 ``ok``；``idle < idle_ms`` 为 ``ok``；
    ``idle_ms <= idle <= idle_ms + grace_ms`` 为 ``warn``（正好到点即超时）；
    超过 ``idle_ms + grace_ms`` 仍无操作为 ``kick``。
    白名单判定先于时长判定，白名单玩家永远 ``ok``。
    """

    def __init__(self, idle_ms=1000, grace_ms=500):
        self.idle_ms = idle_ms
        self.grace_ms = grace_ms
        self.last = {}
        self.whitelist = set()
        self.handled = set()
        self.scanned = 0

    def allow(self, player):
        """把一个玩家放进白名单。"""
        self.whitelist.add(player)

    def touch(self, event_id, player, now_ms):
        """记录一次操作；同一个 ``event_id`` 只生效一次。

        重复上报直接忽略，不改变最近操作时刻。
        """
        if event_id in self.handled:
            return
        self.handled.add(event_id)
        previous = self.last.get(player)
        if previous is None or now_ms > previous:
            self.last[player] = now_ms

    def check(self, player, now_ms):
        """返回 ok / warn / kick，单次摊还 O(1)。"""
        self.scanned += 1
        if player in self.whitelist:
            return "ok"
        last = self.last.get(player)
        if last is None:
            return "ok"
        idle = now_ms - last
        if idle < self.idle_ms:
            return "ok"
        if idle <= self.idle_ms + self.grace_ms:
            return "warn"
        return "kick"

    def scanned_count(self):
        return self.scanned
