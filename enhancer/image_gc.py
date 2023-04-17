from cloudio ipmort ImageIO, OLD_THRESHOLD, BucketConfig
from datetime import datetime, timezone
import json

img_io = ImageIO()

def clean_old(bucket_name, now_ts):
    args = {}
    old_keys = []
    while True:
        response = img_io.s3.list_objects_v2(
            Bucket=bucket_name,
            MaxKeys=1024,
            **args
        )
        if response['KeyCount'] == 0:
            break

        for o in response['Contents']:
            if o['LastModified'] + OLD_THRESHOLD < now_ts:
                old_keys.append(o['Key'])
        if response['IsTruncated'] == False:
            break
        args['ContinuationToken'] = response['NextContinuationToken']
    print(old_keys)
    if len(old_keys) > 0:
        img_io.s3.delete_objects(
            Bucket=bucket_name,
            Delete={
                'Objects': [{'Key': key} for key in old_keys],
                'Quiet': True,
            }
        )

def clean_old_images(event, context):
    now_ts = datetime.now(timezone.utc)
    for bucket_name in [BucketConfig.PREVIEW_BUCKET, BucketConfig.ENHANCE_BUCKET]:
        clean_old(bucket_name, now_ts)
