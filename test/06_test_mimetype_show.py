

image_name = "xx.png"

video_name = "xx.mp4"


from mimetypes import guess_type

# (mimetype类型,压缩格式) = guess_type(文件名称,必须带有后缀名)
print(guess_type(image_name)[0])
print(guess_type(video_name)[0])

images = {"1":1,"2":2}
print(len(images))