import boto3
from botocore import UNSIGNED
from botocore.client import Config
import polars as pl
import os

BUCKET_NAME = "mit-supercloud-dataset"
GPU_PREFIX = "datacenter-challenge/202201/gpu/"
OUT_PREFIX = "new_gpu/"

START_NUM = 1
END_NUM = 100

MAX_SIZE = 800 * 1024 * 1024

out_cols = [
    "utilization_gpu_pct",
    "utilization_memory_pct",
    "memory_free_MiB",
    "memory_used_MiB",
    "temperature_gpu",
    "temperature_memory",
    "power_draw_W",
    "pcie_link_width_current",
    "gpu_index",
]


def main():
    out_cols_means = list(map(lambda col_name: pl.col(col_name).mean(), out_cols))
    c = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    for dir_num in range(START_NUM, END_NUM + 1):
        dir_name = str(dir_num).zfill(4)
        print(f"DOWNLOADING DIR {dir_name}")
        out_dir = os.path.join(OUT_PREFIX, dir_name)
        os.makedirs(out_dir)
        res = c.list_objects(
            Bucket=BUCKET_NAME, Prefix=os.path.join(GPU_PREFIX, dir_name)
        )
        contents_count = len(res["Contents"])
        i = 1
        for content in res["Contents"]:
            file_name = os.path.basename(content["Key"])
            out_path = os.path.join(OUT_PREFIX, dir_name, file_name)
            c.download_file(BUCKET_NAME, content["Key"], out_path)

            out_stat = os.stat(out_path)
            if out_stat.st_size < MAX_SIZE:
                df = pl.read_csv(out_path)
                df = df.with_columns(
                    pl.from_epoch(pl.col("timestamp"), time_unit="s").alias("datetime")
                )
                df = df.sort(by=["gpu_index", "datetime"])
                df = df.group_by_dynamic(
                    index_column="datetime",
                    every="1m",
                    group_by="gpu_index",
                ).agg(out_cols_means)
                out_path_min = out_path.replace(".csv", "_min.csv")
                df.write_csv(out_path_min)
                print(f"({i}/{contents_count}) downloaded {out_path_min}")
            else:
                print(f"{out_path} was to big to download")
            i += 1
            os.remove(out_path)


main()
