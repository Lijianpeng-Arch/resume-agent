#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键停止脚本 - 杀掉 8001-8020 端口上的所有 Python 进程"""
import os
import sys
import subprocess
import platform

IS_WINDOWS = platform.system() == "Windows"


def log(msg=""):
    print(msg, flush=True)


def main():
    log("")
    log("正在停止所有本地服务进程...")

    pids_killed = 0
    NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

    if IS_WINDOWS:
        try:
            r = subprocess.run(
                ["netstat", "-ano", "-p", "TCP"],
                capture_output=True, timeout=3, text=True,
                creationflags=NO_WINDOW,
            )
            pids = set()
            for line in r.stdout.splitlines():
                if "LISTENING" not in line:
                    continue
                for port in range(8001, 8021):
                    if (":" + str(port) + " ") in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            try:
                                pids.add(int(parts[-1]))
                            except ValueError:
                                pass
                        break
            for pid in pids:
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(pid)],
                        capture_output=True, timeout=2,
                        creationflags=NO_WINDOW,
                    )
                    pids_killed += 1
                except Exception:
                    pass
        except Exception as e:
            log("扫描端口失败: " + str(e))
    else:
        for port in range(8001, 8021):
            try:
                subprocess.run(
                    ["fuser", "-k", str(port) + "/tcp"],
                    capture_output=True, timeout=2,
                )
                pids_killed += 1
            except Exception:
                pass

    if pids_killed == 0:
        log("没有发现运行中的服务进程。")
    else:
        log("已停止 " + str(pids_killed) + " 个进程。")

    log("")
    try:
        input("按回车键关闭窗口...")
    except EOFError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())