from PIL import Image, ImageEnhance
from cloudio import ImageIO, BucketConfig
import logging, traceback, sys
import json

img_io = ImageIO()

enhancers = {
    'sharpness': ImageEnhance.Sharpness, 
    'contrast': ImageEnhance.Contrast, 
    'brightness': ImageEnhance.Brightness,
}

def generate_preview_images(img, name):
    w, h = img.width // 48, img.height // 48
    if w < 48:
        w = 48
        h = img.height * w // img.width

    img = img.resize((w, h))
    
    results = []
    for ename, e in enhancers.items():
        factor = 0.2
        while factor <= 1.8:
            str_factor = '%.2f' % factor
            preview_name = f'{ename}_{str_factor}_{name}'
            img_io.write_image(e(img).enhance(factor), preview_name, bucket=BucketConfig.PREVIEW_BUCKET)
            results.append({
                'name': preview_name,
                ename: str_factor
            })
            
            factor += 0.2
    return results

        
def log_exception():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    logging.error(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))

def cors_response(s):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,Access-Control-Allow-Origin',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': s,
    }

def enhance_image(event, context):
    if event['requestContext']['http']['method'] == 'OPTIONS':
        return cors_response('')
    try:
        body = json.loads(event['body'])
        name = body['name']
        img = img_io.read_image(name)
        modified = False
        for ename, e in enhancers.items():
            if ename in body:
                img = e(img).enhance(float(body[ename]))
                modified = True
        if modified:
            img_io.write_image(img, name, bucket=BucketConfig.ENHANCE_BUCKET)
            return cors_response('done')
        else:
            return cors_response(json.dumps(generate_preview_images(img, name)))
    except Exception as e:
        log_exception()
        raise e

