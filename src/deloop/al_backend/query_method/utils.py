import numpy as np


def box_iou(box1, box2):
    # https://github.com/pytorch/vision/blob/master/torchvision/ops/boxes.py
    """
    Return intersection-over-union (Jaccard index) of boxes.
    Both sets of boxes are expected to be in (x1, y1, x2, y2) format.
    Arguments:
        box1 (Array[N, 4])
        box2 (Array[M, 4])
    Returns:
        iou (Array[N, M]): the NxM matrix containing the pairwise
            IoU values for every element in boxes1 and boxes2
    """

    def box_area(box):
        # box = 4xn
        return (box[2] - box[0]) * (box[3] - box[1])

    area1 = box_area(box1.T)
    area2 = box_area(box2.T)

    ious = np.zeros((len(box1), len(box2)))
    for i in range(len(box1)):
        xx1 = np.maximum(box1[i, 0], box2[:, 0])
        yy1 = np.maximum(box1[i, 1], box2[:, 1])
        xx2 = np.minimum(box1[i, 2], box2[:, 2])
        yy2 = np.minimum(box1[i, 3], box2[:, 3])

        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        ovr = inter / (area1[i] + area2 - inter)
        ovr[ovr > 1] = 1

        ious[i] = ovr
    return ious
