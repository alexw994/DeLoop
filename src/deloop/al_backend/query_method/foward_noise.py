import numpy as np
from pathlib import Path
import sys

np.random.seed(0)
noise = np.array(np.random.normal(0, 1, int(1e+8)), np.float32)

FILE = Path(__file__).resolve()
ROOT = FILE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from deloop.al_backend.query_method.utils import box_iou
from deloop.schema import StatusEnum
from PIL import Image


def gasuss_noise(image, mean=0, var=0.001):
    '''
        Add gasuss noise
        mean : mean
        var : variation

        N(0, 1)
        N(mean, var) = mean + sqrt(var) * N(0, 1)
    '''
    image = np.array(image, dtype=np.float32) / 255.

    shape = image.shape
    e = np.random.randint(0, 1e+8 - np.prod(shape))
    image_noise = noise[e: e + np.prod(shape)].reshape(shape)
    sqrt_var = var ** 0.5

    image_noise = image_noise * sqrt_var + mean

    out = image + image_noise
    out = np.clip(out, 0, 1.0) * 255
    out = np.uint8(out)

    return out


def state_calssify(img, model, items=None):
    if items is None:
        items = model.infer(img)

    items_gt_0_4 = [item for item in items if item.confidence > 0.4]

    if len(items_gt_0_4) > 0:
        # 计算max_item_score
        max_item_score = np.max([item.confidence for item in items])
        mean_item_score = np.mean([item.confidence for item in items])

        # 计算uncertainty_score
        uncertainty_score = uncertainty_function(img, model)

        if uncertainty_score < 0.3 and max_item_score > 0.7 and mean_item_score > 0.6:
            state = StatusEnum.AUTO
        else:
            state = StatusEnum.ORA
    else:
        uncertainty_score = None
        state = StatusEnum.INVALID

    return state, uncertainty_score


def uncertainty_function(img, model, times=5):
    boxes = []
    probabilitys = []
    for i in range(times):
        if i == 0:
            noise_img = np.array(img, np.uint8)
        else:
            noise_img = gasuss_noise(img, 0, 0.01 * i)
        noise_img = Image.fromarray(noise_img)
        items = model.infer(noise_img)

        boxes.append(np.array([[item.box.x1,
                                item.box.y1,
                                item.box.x2,
                                item.box.y2] for item in items]))
        probabilitys.append(np.array([item.confidence for item in items]))

    # 对于高置信度的box
    # 如果对于噪声的抵抗能力差，那么不确定性就越高
    location_uncertainty = []
    probability_uncertainty = []
    for t in range(1, times):
        n = len(boxes[0])
        m = len(boxes[t])
        p_uncert = []
        l_uncert = []

        if m != 0:
            # 相对于原来的boxes 有多少改变
            ious = box_iou(boxes[0], boxes[t])
            probs = probabilitys[t]

            # 对于每一个真实框，都要找到一个预测框与之对应
            # 如果找不到 index就为-1
            max_index = []
            for j in range(n):
                if j == 0:
                    max_index.append(ious.argmax(1)[j])
                else:
                    if ious.argmax(1)[j] not in ious.argmax(1)[:j]:
                        max_index.append(ious.argmax(1)[j])
                    else:
                        max_index.append(-1)

            for j in range(n):
                if max_index[j] == -1:
                    # 丢失
                    # 不稳定
                    # 如果更早噪声level就丢失，那么不确定性就高
                    p_uncert.append(1)
                    l_uncert.append(1)
                else:
                    p_uncert.append(max(0, probabilitys[0][j] - probabilitys[t][max_index[j]]))
                    l_uncert.append(max(0, 1 - ious[j, max_index[j]]))

            probability_uncertainty.append(p_uncert)
            location_uncertainty.append(l_uncert)
        else:
            # 如果噪声大到检不出
            probability_uncertainty.append(np.ones(n))
            location_uncertainty.append(np.ones(n))
    location_uncertainty = np.array(location_uncertainty)
    probability_uncertainty = np.array(probability_uncertainty)
    return (0.7 * location_uncertainty.mean(0) + 0.3 * probability_uncertainty.mean(0)).mean()
