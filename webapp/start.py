#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键启动脚本 - 适合小白用户

特性：
1. 自动适配当前文件所在目录（不依赖命令行路径）
2. 自动检测 Python 版本
3. 自动清理残留进程后重启
4. 自动找 8001-8020 空闲端口
5. 中文界面，错误兜底
6. 跨平台：Windows / macOS / Linux
"""
import os
import sys
import time
import socket
import subprocess
import platform

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_PY = os.path.join(SCRIPT_DIR, "server.py")
LOG_PATH = os.path.join(SCRIPT_DIR, "server.log")

IS_WINDOWS = platform.system() == "Windows"


def log(msg=""):
    print(msg, flush=True)


def pause():
    try:
        input("\n按回车键关闭窗口...")
    except EOFError:
        time.sleep(3)


def check_python():
    if sys.version_info < (3, 7):
        log("[错误] 需要 Python 3.7 或更高版本")
        log("       当前版本: Python " + sys.version.split()[0])
        log("       下载地址: https://www.python.org/downloads/")
        log('       安装时请务必勾选 "Add Python to PATH"')
        pause()
        return False
    return True


def check_server_py():
    if not os.path.exists(SERVER_PY):
        log("[错误] 找不到 server.py")
        log("       期望位置: " + SERVER_PY)
        log("       请确认此脚本在 webapp 目录里运行")
        pause()
        return False
    return True


def kill_old_servers():
    """清理 8001-8020 端口上残留的进程"""
    if not IS_WINDOWS:
        for port in range(8001, 8021):
            try:
                subprocess.run(
                    ["fuser", "-k", str(port) + "/tcp"],
                    capture_output=True, timeout=2,
                )
            except Exception:
                pass
        return

    NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

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
            except Exception:
                pass
    except subprocess.TimeoutExpired:
        pass
    except Exception:
        pass


def wait_for_port(timeout_sec=10):
    """探测 8001-8020 哪个端口有 server 在监听"""
    start_time = time.time()
    while time.time() - start_time < timeout_sec:
        for port in range(8001, 8021):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    s.connect(("127.0.0.1", port))
                    return port
            except (OSError, ConnectionRefusedError):
                continue
        time.sleep(0.3)
    return None


def main():
    log("")
    log("=" * 60)
    log("  AI 简历优化 Agent 启动中...")
    log("=" * 60)
    log("  工作目录: " + SCRIPT_DIR)
    log("  Python: " + sys.version.split()[0])
    log("  操作系统: " + platform.system() + " " + platform.release())
    log("=" * 60)
    log("")

    if not check_python():
        return 1
    if not check_server_py():
        return 1

    log("[1/4] 清理旧进程...")
    kill_old_servers()
    time.sleep(0.5)

    log("[2/4] 启动服务...")
    log("       日志文件: " + LOG_PATH)
    try:
        log_file = open(LOG_PATH, "w", encoding="utf-8")
    except Exception as e:
        log("[错误] 无法创建日志文件: " + str(e))
        pause()
        return 1

    try:
        proc = subprocess.Popen(
            [sys.executable, "-u", SERVER_PY],
            cwd=SCRIPT_DIR,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
    except Exception as e:
        log("[错误] 启动失败: " + str(e))
        log_file.close()
        pause()
        return 1

    log("[3/4] 等待服务就绪...")
    port = wait_for_port(timeout_sec=10)

    if not port:
        log("[失败] 服务在 10 秒内没起来")
        log("        请打开日志查看: " + LOG_PATH)
        log("")
        log("        日志内容:")
        log("        " + "-" * 56)
        try:
            log_file.close()
            with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
                log(f.read())
        except Exception:
            pass
        log("        " + "-" * 56)
        log("")
        log("        常见原因:")
        log("        1) 8001-8020 端口全部被其他程序占用")
        log("        2) server.py 本身有错误（看上方日志）")
        log("        3) 防火墙拦截了 Python")
        pause()
        return 1

    url = "http://127.0.0.1:" + str(port) + "/"
    log("[4/4] 服务已就绪！")
    log("")
    log("=" * 60)
    log("  访问地址: " + url)
    log("  进程 PID: " + str(proc.pid))
    log("  日志位置: " + LOG_PATH)
    log("=" * 60)
    log("")
    log("  浏览器应已自动打开；如未打开请手动复制上方地址到浏览器")
    log("  关闭此窗口不会停止服务，请双击 stop.py / stop.cmd 停止")
    log("")

    pause()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        log("\n[用户中断]")
        sys.exit(0)
    except Exception as e:
        log("\n[未捕获错误] " + str(e))
        import traceback
        traceback.print_exc()
        pause()
        sys.exit(1)