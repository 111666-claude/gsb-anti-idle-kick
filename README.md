# anti-idle-kick

挂机踢出：按无操作时长给出 ok / warn / kick，白名单玩家永远例外，只用 Python 标准库。

```
python3 -m idle.cli --sample whitelist
python3 -m idle.cli --sample exact
python3 -m idle.cli --sample grace
python3 -m idle.cli --sample scan
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **到点判定**：距最近一次操作的时间达到 `idle_ms` 就算超时（正好等于算超时）。
- **没有记录**：还没有任何操作记录的玩家一律按 `ok` 处理。
- **宽限状态机**：刚超时返回 `warn`；再等满 `grace_ms` 仍没有操作才返回 `kick`；
  宽限期内任何一次操作都把状态打回 `ok`。
- **白名单覆盖层**：白名单里的玩家永远返回 `ok`，白名单判定先于时长判定。
- **幂等**：同一个 `event_id` 只生效一次，重复上报不改变最近操作时刻。
- **查询代价**：`check` 不许每次全扫玩家表，`scanned_count()` 不随玩家数乘判定次数增长。
- **规模**：50 万玩家、每秒 10 万次判定，单次摊还 O(1)。

## 输出契约（不改格式）

```
result=..
scanned=..
```

## 目录

```
idle/core.py   时长判定、宽限状态机与白名单
idle/cli.py    命令行入口
tests/         unittest 用例
```
