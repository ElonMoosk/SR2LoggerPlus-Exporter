#!/usr/bin/env python3
"""SR2LoggerPlus UDP 接收端：接收 Sample 与 Log 消息，写出 JSONL/CSV。"""

import json
import os
import re
import socket
import struct
import sys
import time

HOST = "127.0.0.1"
PORT = 2837
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "flight.jsonl")
LOG = os.path.join(HERE, "messages.txt")

TYPE_FORMATS = {0: "", 1: "d", 2: "?", 3: "ddd"}

STATE_FIELDS = [
    "时间", "高度", "高度ASL", "平速", "垂速",
    "X", "Y", "Z", "VX", "VY", "VZ",
    "纬度", "经度", "距靶", "地形高度",
]

GUID_FIELDS = [
    "时间", "纵差", "横差", "预测距", "俯仰", "倾侧", "推力",
    "燃料", "气密", "阻力", "俯仰角", "滚转目标", "攻角",
]

# 长度 -> (行类型, 字段表)
SCHEMAS = {
    len(STATE_FIELDS): ("state", STATE_FIELDS),
    len(GUID_FIELDS): ("guid", GUID_FIELDS),
}

# 带文本标签的行：WAIT,<秒> / LAND,<纬度>,<经度>,<距靶米>
TAGGED = {
    "WAIT": ["等待秒"],
    "LAND": ["纬度", "经度", "距靶"],
    "GD": ["时间", "高度", "纵差", "横差", "滚转目标", "倾侧", "进场比例", "滚转输入", "滚转速率", "俯仰", "航向", "俯仰速率", "偏航速率"],
    "ZLT": ["时间", "高度", "平速", "垂速", "俯仰", "倾侧", "航向", "滚转输入", "偏航输入", "距靶"],
    "FD": ["时间", "质量", "当前推力", "最大推力", "推重比", "余油", "阻力", "马赫", "加速度", "攻角", "侧滑"],
}

PREFIX = re.compile(r"^\[([^\]]+)\]\s*<(-?\d+)>:\s?(.*)$")


class Packet:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def get(self, n):
        self.pos += n
        return self.data[self.pos - n:self.pos]

    def read(self, fmt):
        if not fmt:
            return None
        vals = struct.unpack(fmt, self.get(struct.calcsize(fmt)))
        return vals[0] if len(vals) == 1 else vals

    @property
    def more(self):
        return self.pos < len(self.data)


def parse_line(msg):
    """把 log 消息里的 CSV 行转成 dict，不是 CSV 返回 None。"""
    m = PREFIX.match(msg)
    payload = m.group(3) if m else msg
    parts = payload.split(",")
    tag = parts[0].strip()
    if tag in TAGGED and len(parts) == len(TAGGED[tag]) + 1:
        try:
            vals = [float(p) for p in parts[1:]]
        except ValueError:
            return None
        rec = {"kind": tag.lower()}
        rec.update(zip(TAGGED[tag], vals))
        rec["t"] = m.group(1) if m else ""
        return rec
    schema = SCHEMAS.get(len(parts))
    if schema is None:
        return None
    kind, fields = schema
    try:
        vals = [float(p) for p in parts]
    except ValueError:
        return None
    rec = {"kind": kind}
    rec.update(zip(fields, vals))
    rec["t"] = m.group(1) if m else ""
    return rec


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((HOST, PORT))
    except OSError as e:
        print(f"无法绑定 {HOST}:{PORT} -> {e}")
        print("是不是已经开了一个接收端？关掉重复的进程再试。")
        return 1

    print(f"监听 udp://{HOST}:{PORT}")
    print(f"CSV 数据 -> {OUT}")
    print(f"原始消息 -> {LOG}")
    print("等待游戏数据…… (Ctrl+C 结束)\n")

    lines = 0
    with open(OUT, "a", encoding="utf-8") as fout, open(LOG, "a", encoding="utf-8") as flog:
        while True:
            try:
                data, _addr = sock.recvfrom(65535)
            except KeyboardInterrupt:
                break
            try:
                p = Packet(data)
                kind = p.read("B")
                if kind == 1:
                    ts = p.read("Q")
                    rec = {"t_ms": ts}
                    while p.more:
                        name_len = p.read("I")
                        name = p.get(name_len).decode("utf-8", "replace")
                        tp = p.read("B")
                        if tp == 4:
                            text_len = p.read("I")
                            val = p.get(text_len).decode("utf-8", "replace")
                        else:
                            val = p.read(TYPE_FORMATS.get(tp, ""))
                        rec[name] = val
                    if len(rec) > 1:
                        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        fout.flush()
                elif kind == 2:
                    msg_len = p.read("I")
                    msg = p.get(msg_len).decode("utf-8", "replace")
                    flog.write(msg + "\n")
                    flog.flush()
                    rec = parse_line(msg)
                    if rec is not None:
                        rec["wall"] = round(time.time(), 3)
                        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        fout.flush()
                        lines += 1
                        if lines % 10 == 0 and rec.get("kind") == "state":
                            print(
                                f"[{lines}] 高度={rec['高度']:.0f}"
                                f" 地形={rec['地形高度']:.0f}"
                                f" 距靶={rec['距靶']:.0f}"
                            )
            except Exception as e:
                print("解析失败:", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())

