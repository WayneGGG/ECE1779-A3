from PIL import Image, ImageEnhance
from cloudio import ImageIO

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

def enhance_image(event, context):
    name = event['name']
    img = img_io.read_image(name)
    modified = False
    for ename, e in enhancers.items():
        if ename in event:
            img = e(img).enhance(float(event[ename]))
            modified = True
    if modified:
        img_io.write_image(img, name, bucket=BucketConfig.ENHANCE_BUCKET)
        return []
    else:
        return generate_preview_images(img, name)

