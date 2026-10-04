"""挂机踢出：按无操作时长给出 ok / warn / kick，白名单玩家永远例外。

判定口径（以 README 为准）：

- 白名单玩家永远 ``ok``，白名单判定先于时长判定。
- 没有任何操作记录的玩家按 ``ok`` 处理。
- ``now - last < idle_ms``                        -> ``ok``
- ``idle_ms <= now - last <= idle_ms + grace_ms`` -> ``warn``（两端边界都算 warn）
- ``now - last > idle_ms + grace_ms``             -> ``kick``
- 宽限期内任意一次（非重复的）操作刷新最近操作时刻，状态打回 ``ok``。
- 同一个 ``event_id`` 只生效一次，重复上报不改变任何状态。

所有操作都是单次哈希表访问，摊还 O(1)，``check`` 不扫玩家表。
"""


class IdleGuard:
    """挂机判定台账。"""

    def __init__(self, idle_ms=1000, grace_ms=500):
        self.idle_ms = idle_ms
        self.grace_ms = grace_ms
        self.last = {}
        self.whitelist = set()
        #: 已生效的 event_id，用于幂等去重
        self.handled = set()
        self.scanned = 0

    def allow(self, player):
        """把一个玩家放进白名单。"""
        self.whitelist.add(player)

    def touch(self, event_id, player, now_ms):
        """记录一次操作；重复 event_id 直接忽略，不改变最近操作时刻。"""
        if event_id in self.handled:
            return
        self.handled.add(event_id)
        self.last[player] = now_ms
        self.scanned += 1

    def check(self, player, now_ms):
        """返回 ok / warn / kick；白名单优先，单次哈希查询，不扫全表。"""
        if player in self.whitelist:
            return "ok"
        last = self.last.get(player)
        if last is None:
            return "ok"
        elapsed = now_ms - last
        if elapsed < self.idle_ms:
            return "ok"
        if elapsed <= self.idle_ms + self.grace_ms:
            return "warn"
        return "kick"

    def scanned_count(self):
        return self.scanned
