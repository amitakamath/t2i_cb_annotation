import os
import json
import random

files = os.listdir('study_images/qwen')
assert set(files)==set(os.listdir('study_images/sd2_1'))
assert set(files)==set(os.listdir('study_images/sd35_large'))

new_files = ['study_images/qwen/{}'.format(f) for f in files]
new_files.extend(['study_images/sd2_1/{}'.format(f) for f in files])
new_files.extend(['study_images/sd35_large/{}'.format(f) for f in files])

import pdb
pdb.set_trace()

random.shuffle(new_files)
captions = [f.split('.')[0].split('/')[-1].split('_')[0] for f in new_files]
models = [f.split('.')[0].split('/')[-2] for f in new_files]

fp = open('image_data.csv', 'w')

for img, cap, model in zip(new_files, captions, models):
    fp.write('{},{},{},0\n'.format(img, model, cap))


