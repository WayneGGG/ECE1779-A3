import boto3
from io import BytesIO
from datetime import timedelta
from PIL import Image

class BucketConfig:
    DEFAULT_BUCKET = 'imagefilesbucket20230312222008826009'
    PREVIEW_BUCKET = 'a3-preview-20230409'
    ENHANCE_BUCKET = 'a3-enhance-20230409'

class ImageIO:
    def __init__(self):
        self.s3 = boto3.client('s3')

        for bucket_name in [BucketConfig.DEFAULT_BUCKET, BucketConfig.PREVIEW_BUCKET, BucketConfig.ENHANCE_BUCKET]:
            self.s3.create_bucket(Bucket=bucket_name)
    
    def read_image(self, name, bucket=BucketConfig.DEFAULT_BUCKET):
        response = self.s3.get_object(Bucket=bucket, Key=name)
        return Image.open(response['Body'])

    def write_image(self, img, name, bucket=BucketConfig.DEFAULT_BUCKET):
        buffer = BytesIO()
        extname = 'png'
        if name.lower().endswith('.jpg') or name.lower().endswith('.jpeg'):
            extname = 'jpeg'
        elif name.lower().endswith('.gif'):
            extname = 'gif'
        img.save(buffer, extname)
        buffer.seek(0)
        response = self.s3.put_object(Bucket=bucket, Key=name, Body=buffer, ACL='public-read') # LOL
        assert response['ResponseMetadata']['HTTPStatusCode'] == 200, 'Fail to upload to S3'

        
OLD_THRESHOLD=timedelta(minutes=10)

