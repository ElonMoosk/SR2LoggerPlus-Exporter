# SR2 Logger Plus — 飞行日志导出工具 / Flight Log Exporter

把《Juno: New Origins (SimpleRockets 2)》里的飞行遥测数据实时导出为结构化文件，
用于分析火箭的制导、姿态和着陆性能。

Exports live flight telemetry from *Juno: New Origins (SimpleRockets 2)* into structured
files for analyzing guidance, attitude and landing performance.

> 纯本地运行，只监听 `127.0.0.1:2837`，**不联网、不上传任何数据**。
> Fully local: only listens on `127.0.0.1:2837`. **No network, no upload.**

---

## 一键安装 / One-click install

1. 下载本仓库 / Download this repo（`Code` → `Download ZIP`）
2. **双击 `install.bat`** / **double-click `install.bat`**
3. 按提示完成 / follow the prompts
4. 安装游戏模组 / install the game mod:
   https://www.simplerockets.com/Mods/View/64864/SR2LoggerPlus
5. 双击桌面「启动日志接收端」 / double-click the desktop shortcut

看到这行就成功了 / Ready when you see:

```
监听 udp://127.0.0.1:2837
```

**安装位置 / Install location:**

```
%USERPROFILE%\AppData\LocalLow\Jundroo\SimpleRockets 2\UserData\SR2LoggerPlus\
```

装在游戏用户数据目录内，AI 助手或其他工具可直接找到。
Inside the game's user-data folder, so assistants/tools can find it directly.

---

## 它做什么 / What it does

```
游戏内 Vizzy 广播 / In-game Vizzy broadcasts
      ↓  模组 SR2LoggerPlus / mod SR2LoggerPlus
  UDP 127.0.0.1:2837
      ↓
  sr2_logger.py
      ↓
  ├─ flight.jsonl   结构化数据 / structured JSONL
  └─ messages.txt   原始消息 / raw messages
```

---

## 输出格式 / Output formats

### 固定字段行（按逗号个数识别）/ Fixed-field rows (by field count)

| 字段数 Count | kind | 字段 Fields |
|---|---|---|
| 15 | `state` | 时间, 高度, 高度ASL, 平速, 垂速, X, Y, Z, VX, VY, VZ, 纬度, 经度, 距靶, 地形高度 |
| 13 | `guid` | 时间, 纵差, 横差, 预测距, 俯仰, 倾侧, 推力, 燃料, 气密, 阻力, 俯仰角, 滚转目标, 攻角 |

### 带标签行（`标签,数值,...`）/ Tagged lines (`TAG,value,...`)

| 标签 Tag | 字段 Fields |
|---|---|
| `WAIT` | 等待秒 seconds |
| `LAND` | 纬度, 经度, 距靶 |
| `GD` | 时间, 高度, 纵差, 横差, 滚转目标, 倾侧, 进场比例, 滚转输入, 滚转速率, 俯仰, 航向, 俯仰速率, 偏航速率 |
| `ZLT` | 时间, 高度, 平速, 垂速, 俯仰, 倾侧, 航向, 滚转输入, 偏航输入, 距靶 |
| `FD` | 时间, 质量, 当前推力, 最大推力, 推重比, 余油, 阻力, 马赫, 加速度, 攻角, 侧滑 |

**在自己的 Vizzy 程序里**，用「向附近载具广播」发出符合上述格式的字符串即可被自动记录。
**In your own Vizzy program**, broadcast strings in the formats above to have them recorded.

---

## 分析示例 / Analysis examples

```python
import json

rows = []
with open("flight.jsonl", encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        if r.get("kind") == "state":
            rows.append(r)

for r in rows[-20:]:
    print(r["t"], "高度 alt", r["高度"], "距靶 miss", r["距靶"])
```

转 CSV 给 Excel / Convert to CSV for Excel:

```python
import json, csv

rows = [json.loads(l) for l in open("flight.jsonl", encoding="utf-8")]
rows = [r for r in rows if r.get("kind") == "state"]

with open("flight.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
```

> Excel 请用 `utf-8-sig`，否则中文列名乱码。
> Use `utf-8-sig` for Excel, otherwise Chinese headers get garbled.

---

## 常见问题 / FAQ

**启动报「无法绑定 127.0.0.1:2837」/ Cannot bind 127.0.0.1:2837**
已经有一个接收端在跑，关掉重复的 `python.exe`。
Another receiver is already running; kill the duplicate `python.exe`.

**能启动但文件一直是空的 / Starts but files stay empty**
1. 模组没装或没启用 / mod not installed or disabled
2. 端口不是 2837（改 `sr2_logger.py` 顶部的 `PORT`）/ wrong port
3. Vizzy 程序里没发广播 / no broadcasts emitted

**行被跳过（不报错）/ Lines silently skipped**
字段数不对。固定行必须是 15 或 13 个字段；标签行必须与上表一致。
Wrong field count: fixed rows need 15 or 13 fields; tagged rows must match the table.

**中文乱码 / Garbled Chinese**
用 UTF-8 打开；Excel 用上面的脚本转成 `utf-8-sig`。
Open as UTF-8; for Excel convert with `utf-8-sig` as shown above.

---

## 自定义 / Customization

改 `sr2_logger.py` 顶部 / Edit the top of `sr2_logger.py`:

```python
HOST = "127.0.0.1"
PORT = 2837
OUT  = os.path.join(HERE, "flight.jsonl")
LOG  = os.path.join(HERE, "messages.txt")
```

新增数据格式 / Add a new format:

```python
TAGGED = {
    "MYTAG": ["field1", "field2", "field3"],
}
```

之后程序里发 `MYTAG,1,2,3` 就会被解析。
Then broadcasting `MYTAG,1,2,3` will be parsed.

---

## 文件说明 / Files

| 文件 File | 作用 Purpose |
|---|---|
| `install.bat` | 一键安装器 / one-click installer (checks Python, deploys, creates shortcut) |
| `sr2_logger.py` | 接收端主程序 / UDP receiver |
| `start_logger.bat` | 通用启动脚本 / portable launcher |
| `使用说明.md` | 详细中文+英文说明书 / detailed bilingual guide |

---

## 卸载 / Uninstall

删除 `%USERPROFILE%\AppData\LocalLow\Jundroo\SimpleRockets 2\UserData\SR2LoggerPlus\`
和桌面快捷方式即可，不写注册表。
Delete that folder and the desktop shortcut. Nothing is written to the registry.

---

## 许可 / License

MIT
