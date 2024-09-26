import boto3
from botocore import UNSIGNED
from botocore.client import Config
import os

BUCKET_NAME = "mit-supercloud-dataset"
CPU_PREFIX = "datacenter-challenge/202201/cpu/"
OUT_PREFIX = "cpu/"

START_NUM = 1
END_NUM = 100


def main():
    c = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    for dir_num in range(START_NUM, END_NUM + 1):
        dir_name = str(dir_num).zfill(4)
        print(f"DOWNLOADING DIR {dir_name}")
        out_dir = os.path.join(OUT_PREFIX, dir_name)
        os.makedirs(out_dir)
        res = c.list_objects(
            Bucket=BUCKET_NAME, Prefix=os.path.join(CPU_PREFIX, dir_name)
        )
        contents_count = len(res["Contents"])
        i = 1
        for content in res["Contents"]:
            file_name = os.path.basename(content["Key"])
            if file_name.endswith("-summary.csv"):
                out_path = os.path.join(OUT_PREFIX, dir_name, file_name)
                c.download_file(BUCKET_NAME, content["Key"], out_path)
                print(f"({i}/{contents_count}) downloaded {out_path}")
                i += 1


main()
