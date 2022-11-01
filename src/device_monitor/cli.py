from argparse import ArgumentParser, Namespace
import os
import time
from typing import List
import logging
import logging.handlers
import psutil
import device_monitor as dm


def main():
    args: Namespace

    args = parse_args()
    if args.version:
        print(f"device-monitor: {dm.__version__}")
    else:
        start_logging(args)


def parse_args() -> Namespace:
    parser: ArgumentParser

    parser = ArgumentParser(description=
"""デバイスを監視してログを記録します。
結果はCSV形式で表示されます。
終了するには「Ctrl」+「C」を入力します。

形式: <タイムスタンプ>,<メモリの合計>,<メモリの使用量>,<メモリの利用可能量>,<メモリの未使用量>,<仮想CPU数>,<CPU利用率1[%]>,...,<ディスク数>,<ディスクマウントポイント1>,<ディスク合計量1>,<ディスク使用量1>,<ディスク未使用量1>,...
""")
    parser.add_argument("--version", "-v", action="store_true", help="バージョンを確認します")
    parser.add_argument("--interval", type=float, default=1.0, help="ログをとる間隔[秒]を指定します. default=1.0")
    parser.add_argument("--path", type=str, default="./log/device.log", help="ログファイルのパスを指定します. default=\"./log/device.log\"")
    parser.add_argument("--period", type=int, default=3600, help="ログのローテーション間隔[秒]を指定します. default=3600")
    parser.add_argument("--backup", type=int, default=3, help="ログのローテーションのバックアップの数を指定します. default=3")
    return parser.parse_args()


def start_logging(args: Namespace):
    interval: float = args.interval
    path: str = os.path.abspath(args.path)
    period: int = args.period
    backup: int = args.backup

    if interval <= 0.0:
        raise RuntimeError("interval should have positive value")
    os.makedirs(os.path.dirname(path), exist_ok=True)

    formatter: logging.Formatter = logging.Formatter("%(created)s,%(message)s")

    handler_stream: logging.Handler = logging.handlers.TimedRotatingFileHandler(path, when="S", interval=period, backupCount=backup, encoding="utf8", delay=False)
    handler_stream.setLevel(logging.DEBUG)
    handler_stream.setFormatter(formatter)

    handler_file: logging.Handler = logging.StreamHandler()
    handler_file.setLevel(logging.DEBUG)
    handler_file.setFormatter(formatter)

    logger: logging.Logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler_stream)
    logger.addHandler(handler_file)

    print("==== START ====")
    print("QUIT: Ctrl + C")
    try:
        count_cpu: int = psutil.cpu_count(logical=True)
        partitions = psutil.disk_partitions()
        t_start = time.time()
        count = 0
        while True:
            pers_cpu: List[float] = psutil.cpu_percent(percpu=True)
            mem = psutil.virtual_memory()
            disks: List[str] = []
            for part in partitions:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(f"\"{part.mountpoint}\",{usage.total},{usage.used},{usage.free}")
            logger.info(
                f"{mem.total},{mem.used},{mem.available},{mem.free},{count_cpu},"
                + ",".join([str(e) for e in pers_cpu])
                + f",{len(partitions)},"
                + ",".join(disks)
            )
            count += 1
            time.sleep(max(0, t_start + interval * count - time.time()))
    except KeyboardInterrupt:
        pass
    finally:
        print("==== QUIT ====")

